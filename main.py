
import os
import re
from pathlib import Path

import httpx
from dotenv import load_dotenv
from pdf_report import create_pdf_report


# ==================================================
# 1. CONFIGURATION
# ==================================================

load_dotenv()

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434",
).rstrip("/")

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:3b",
)

OLOSTEP_API_KEY = os.getenv("OLOSTEP_API_KEY")

MAX_SEARCH_RESULTS = 3

# Intelligent chunking settings
CHUNK_SIZE = 3000
CHUNK_OVERLAP = 300
TOP_CHUNKS_PER_SOURCE = 2

REPORT_FILE = Path("research_report.md")


# ==================================================
# 2. LOCAL AI MODEL - OLLAMA
# ==================================================

def ask_local_ai(prompt: str) -> str:
    """Send a prompt to the local Ollama model."""

    url = f"{OLLAMA_BASE_URL}/api/generate"

    try:
        response = httpx.post(
            url,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=300.0,
        )

        response.raise_for_status()
        data = response.json()

        answer = data.get("response", "").strip()

        if not answer:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        return answer

    except httpx.ConnectError as exc:
        raise RuntimeError(
            "Cannot connect to Ollama. Make sure Ollama is "
            "running and the model is installed."
        ) from exc

    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Ollama returned HTTP {exc.response.status_code}: "
            f"{exc.response.text[:500]}"
        ) from exc


# ==================================================
# 3. OLOSTEP API
# ==================================================

def olostep_headers() -> dict:
    """Create headers for authenticated Olostep requests."""

    if not OLOSTEP_API_KEY:
        raise RuntimeError(
            "OLOSTEP_API_KEY is missing. Add it to your .env file."
        )

    return {
        "Authorization": f"Bearer {OLOSTEP_API_KEY}",
        "Content-Type": "application/json",
    }


# ==================================================
# 4. WEB SEARCH
# ==================================================

def search_web(query: str) -> list[dict]:
    """Search the web using the Olostep API."""

    print("\n[Manager] Searching the web...")

    url = "https://api.olostep.com/v1/searches"

    try:
        response = httpx.post(
            url,
            headers=olostep_headers(),
            json={"query": query},
            timeout=60.0,
        )

        response.raise_for_status()
        data = response.json()

    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Olostep search failed: {exc}"
        ) from exc

    result = data.get("result") or data
    links = result.get("links", [])

    sources = []

    for item in links:
        source_url = item.get("url")

        if not source_url:
            continue

        sources.append({
            "title": item.get("title") or "Untitled webpage",
            "url": source_url,
            "description": item.get("description") or "",
            "content": "",
        })

        if len(sources) >= MAX_SEARCH_RESULTS:
            break

    print(
        f"[Manager] Found {len(sources)} usable search results."
    )

    for index, source in enumerate(sources, start=1):
        print(f"  S{index}: {source['title']}")
        print(f"      {source['url']}")

    return sources


# ==================================================
# 5. SCRAPE WEBPAGES
# ==================================================

def scrape_webpage(source: dict) -> dict:
    """Extract webpage text using the Olostep scrape API."""

    url = "https://api.olostep.com/v1/scrapes"

    try:
        response = httpx.post(
            url,
            headers=olostep_headers(),
            json={
                "url_to_scrape": source["url"],
                "formats": ["markdown"],
            },
            timeout=120.0,
        )

        response.raise_for_status()
        data = response.json()

    except httpx.HTTPError as exc:
        print(
            f"[Scraper] Failed to read {source['url']}: {exc}"
        )

        source["content"] = ""
        source["extraction_error"] = str(exc)

        return source

    result = data.get("result") or data

    content = (
        result.get("markdown_content")
        or result.get("text_content")
        or ""
    )

    if isinstance(content, dict):
        content = (
            content.get("markdown")
            or content.get("text")
            or ""
        )

    source["content"] = str(content).strip()

    if source["content"]:
        print(
            f"[Scraper] Read {source['title']} "
            f"({len(source['content']):,} characters)."
        )
    else:
        print(
            f"[Scraper] No readable text returned for "
            f"{source['title']}."
        )

    return source


# ==================================================
# 6. INTELLIGENT WEBPAGE CHUNKING
# ==================================================

def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split long text into overlapping chunks."""

    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Prefer ending near a sentence boundary.
        if end < len(text):
            boundary = text.rfind(
                ". ",
                start + chunk_size // 2,
                end,
            )

            if boundary != -1:
                end = boundary + 1

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)

    return chunks


def score_chunk(
    question: str,
    chunk: str,
) -> int:
    """Estimate how relevant a chunk is to the question."""

    stopwords = {
        "a", "an", "and", "are", "as", "at", "be", "by",
        "for", "from", "how", "in", "into", "is", "it",
        "of", "on", "or", "the", "this", "to", "was",
        "what", "when", "where", "which", "who", "why",
        "with", "latest", "developments",
    }

    question_terms = {
        word.lower()
        for word in re.findall(
            r"\b[a-zA-Z0-9]+\b",
            question,
        )
        if len(word) > 2 and word.lower() not in stopwords
    }

    chunk_terms = {
        word.lower()
        for word in re.findall(
            r"\b[a-zA-Z0-9]+\b",
            chunk,
        )
    }

    overlap_score = len(question_terms & chunk_terms)

    if question_terms:
        coverage_score = int(
            10 * overlap_score / len(question_terms)
        )
    else:
        coverage_score = 0

    return overlap_score * 10 + coverage_score


def select_relevant_chunks(
    question: str,
    text: str,
    top_k: int = TOP_CHUNKS_PER_SOURCE,
) -> list[str]:
    """Select the most relevant chunks from a webpage."""

    chunks = split_into_chunks(text)

    if not chunks:
        return []

    ranked_chunks = sorted(
        enumerate(chunks),
        key=lambda item: score_chunk(question, item[1]),
        reverse=True,
    )

    selected = ranked_chunks[:top_k]

    # Restore the selected chunks to original page order.
    selected.sort(key=lambda item: item[0])

    return [
        f"[Webpage section {index + 1}]\n{chunk}"
        for index, chunk in selected
    ]


# ==================================================
# 7. READ AND SELECT RELEVANT SOURCES
# ==================================================

def read_sources(
    sources: list[dict],
    question: str,
) -> list[dict]:
    """Read webpages and select relevant sections."""

    print("\n[Manager] Reading webpages...")

    readable_sources = []

    for source in sources:
        extracted = scrape_webpage(source)

        full_text = extracted.get("content", "")

        if not full_text:
            continue

        extracted["full_content_length"] = len(full_text)

        selected_chunks = select_relevant_chunks(
            question,
            full_text,
        )

        if not selected_chunks:
            continue

        # Keep the full length for reporting but send only
        # the selected relevant sections to the AI agents.
        extracted["content"] = "\n\n".join(selected_chunks)
        extracted["selected_chunk_count"] = len(selected_chunks)

        readable_sources.append(extracted)

        print(
            f"[Manager] Selected {len(selected_chunks)} relevant "
            f"sections from {source['title']} "
            f"({len(full_text):,} characters extracted)."
        )

    print(
        f"\n[Manager] Prepared {len(readable_sources)} of "
        f"{len(sources)} webpages for analysis."
    )

    return readable_sources


# ==================================================
# 8. ANALYST AGENT
# ==================================================

def analyst_agent(
    question: str,
    sources: list[dict],
) -> str:
    """Analyze the selected webpage evidence."""

    print("\n[Analyst] Analyzing the evidence...")

    evidence_sections = []

    for index, source in enumerate(sources, start=1):
        evidence_sections.append(
            f"""
SOURCE ID: S{index}
TITLE: {source['title']}
URL: {source['url']}

SELECTED WEBPAGE SECTIONS:
{source['content']}
"""
        )

    evidence = "\n\n".join(evidence_sections)

    prompt = f"""
You are the Analyst agent in a multi-agent research assistant.

RESEARCH QUESTION:
{question}

AVAILABLE WEB EVIDENCE:
{evidence}

Analyze the supplied evidence and prepare a structured report.

Rules:
1. Use only the evidence supplied in this prompt.
2. Do not invent facts, statistics, dates, quotations, or URLs.
3. Attach the correct source ID and URL to important findings.
4. Use exact quotations only if their wording appears in the text.
5. Distinguish source-supported facts from your interpretation.
6. Identify disagreements and evidence gaps.
7. The supplied text contains selected sections, not necessarily
   every section of each webpage. Do not imply that you read
   portions that were not supplied.
8. If evidence is insufficient, say so explicitly.

Use these headings:

# Analyst Findings

## Key Findings

## Supporting Evidence

## Conflicting Evidence

## Evidence Gaps

## Preliminary Conclusion
"""

    analysis = ask_local_ai(prompt)

    print("[Analyst] Analysis completed.")

    return analysis


# ==================================================
# 9. JUDGE AGENT
# ==================================================

def judge_agent(
    question: str,
    analysis: str,
    sources: list[dict],
) -> str:
    """Review findings against the selected source text."""

    print("\n[Judge] Reviewing the findings...")

    source_sections = []

    for index, source in enumerate(sources, start=1):
        source_sections.append(
            f"""
SOURCE ID: S{index}
TITLE: {source['title']}
URL: {source['url']}

SELECTED EXTRACTED TEXT:
{source['content']}
"""
        )

    source_evidence = "\n\n".join(source_sections)

    prompt = f"""
You are the Judge agent in a multi-agent research assistant.

RESEARCH QUESTION:
{question}

ANALYST REPORT:
{analysis}

ORIGINAL SELECTED SOURCE TEXT:
{source_evidence}

Review the analyst report critically.

Requirements:
1. Check claims against the supplied source text.
2. Check source IDs and URLs.
3. Flag unsupported or partially supported claims.
4. Flag quotations that do not match the supplied text.
5. Identify conflicts and limitations.
6. Do not invent evidence or claim to have browsed independently.
7. A plausible statement is not automatically a verified fact.
8. Remember that only selected webpage sections were supplied.

Use these main headings:

# Reviewed Research Report

## Verified Findings

## Unverified or Weakly Supported Claims

## Conflicting Evidence

## Limitations

## Conclusion
"""

    reviewed_report = ask_local_ai(prompt)

    print("[Judge] Review completed.")

    return reviewed_report


# ==================================================
# 10. PYTHON QUOTATION CHECKER
# ==================================================

def verify_quoted_evidence(
    report: str,
    sources: list[dict],
) -> list[dict]:
    """Check whether longer quotations appear in selected text."""

    results = []

    source_lookup = {
        f"S{index}": source
        for index, source in enumerate(sources, start=1)
    }

    quotation_pattern = r'"([^"\n]{20,})"|“([^”\n]{20,})”'

    quotations = re.findall(quotation_pattern, report)

    for pair in quotations:
        quotation = next(
            (part for part in pair if part),
            "",
        ).strip()

        if not quotation:
            continue

        normalized_quote = " ".join(
            quotation.split()
        ).casefold()

        matched_source = None

        for source_id, source in source_lookup.items():
            page_text = " ".join(
                source.get("content", "").split()
            ).casefold()

            if normalized_quote in page_text:
                matched_source = {
                    "source_id": source_id,
                    "title": source["title"],
                    "url": source["url"],
                }
                break

        if matched_source:
            results.append({
                "quotation": quotation,
                "status": "EXACT TEXT MATCH",
                "matched_source": matched_source,
            })
        else:
            results.append({
                "quotation": quotation,
                "status": "NOT FOUND IN SELECTED TEXT",
                "matched_source": None,
            })

    return results


# ==================================================
# 11. MANAGER AGENT
# ==================================================

def manager_agent(question: str) -> str:
    """Coordinate the complete research workflow."""

    print("\n" + "=" * 60)
    print("MULTI-AGENT RESEARCH ASSISTANT")
    print("=" * 60)

    print(f"\nResearch question: {question}")

    # Step 1: Search.
    sources = search_web(question)

    if not sources:
        return (
            "# Research Report\n\n"
            f"## Research Question\n{question}\n\n"
            "No usable search results were returned. "
            "Check the API key, access, and query."
        )

    # Step 2: Extract and select relevant chunks.
    readable_sources = read_sources(
        sources,
        question,
    )

    if not readable_sources:
        return (
            "# Research Report\n\n"
            f"## Research Question\n{question}\n\n"
            "Search results were found, but no readable webpage "
            "text was extracted."
        )

    # Step 3: Analyst.
    analysis = analyst_agent(
        question,
        readable_sources,
    )

    # Step 4: Judge.
    reviewed_report = judge_agent(
        question,
        analysis,
        readable_sources,
    )

    # Step 5: Check quotations in the analyst report.
    quote_checks = verify_quoted_evidence(
        analysis,
        readable_sources,
    )

    print("\n[Evidence Check] Results:")

    if not quote_checks:
        print(
            "No sufficiently long quoted excerpts were detected."
        )

    for check in quote_checks:
        print(
            f"- {check['status']}: "
            f"{check['quotation'][:100]}"
        )

    verified_count = sum(
        check["status"] == "EXACT TEXT MATCH"
        for check in quote_checks
    )

    print(
        f"\n[Evidence Check] {verified_count} of "
        f"{len(quote_checks)} quotations matched the "
        "selected webpage text."
    )

    # Step 6: Format quotation results.
    quote_lines = []

    for check in quote_checks:
        line = (
            f"- **{check['status']}** — "
            f'"{check["quotation"]}"'
        )

        matched_source = check.get("matched_source")

        if matched_source:
            line += (
                f" (Source: {matched_source['source_id']}, "
                f"{matched_source['url']})"
            )

        quote_lines.append(line)

    quote_results = "\n".join(quote_lines)

    if not quote_results:
        quote_results = "- No quotations were checked."

    # Step 7: Format source list.
    source_lines = []

    for index, source in enumerate(
        readable_sources,
        start=1,
    ):
        source_lines.append(
            f"- **S{index}: {source['title']}**\n"
            f"  URL: {source['url']}\n"
            f"  Characters extracted: "
            f"{source.get('full_content_length', 0):,}\n"
            f"  Relevant sections selected: "
            f"{source.get('selected_chunk_count', 0)}"
        )

    source_list = "\n".join(source_lines)

    # Step 8: Assemble report.
    report = (
        "# Research Report\n\n"
        f"## Research Question\n{question}\n\n"
        "## Reviewed Findings\n\n"
        f"{reviewed_report}\n\n"
        "## Automatic Quotation Checks\n\n"
        f"{quote_results}\n\n"
        "## Sources Read\n\n"
        f"{source_list}\n\n"
        "## Methodology\n\n"
        f"- Local model: {OLLAMA_MODEL}\n"
        f"- Webpages successfully extracted: "
        f"{len(readable_sources)} of {len(sources)}\n"
        "- Web search and extraction: Olostep API\n"
        "- Analysis and review: local Ollama model\n"
        "- Chunk selection: Python keyword-overlap scoring\n"
        "- Quotation presence check: Python\n\n"
        "## Important Note\n\n"
        "Quotation matching checks for text within the selected "
        "sections only. A quotation not found there might exist "
        "elsewhere on the original webpage. A text match alone "
        "does not prove that a claim is true or that the quotation "
        "is accurate in its original context.\n"
    )

    return report


# ==================================================
# 12. SAVE REPORT
# ==================================================

def save_report(report: str) -> None:
    """Save the report to a Markdown file."""

    REPORT_FILE.write_text(
        report,
        encoding="utf-8",
    )

    print(
        f"\n[Manager] Report saved to: "
        f"{REPORT_FILE.resolve()}"
    )


# ==================================================
# 13. PROGRAM ENTRY POINT
# ==================================================

def main() -> None:
    """Run the research assistant."""

    print("=" * 60)
    print("FREE MULTI-AGENT RESEARCH ASSISTANT")
    print("=" * 60)
    print(f"Local model: {OLLAMA_MODEL}")
    print("Inference: Local Ollama")
    print("Web research: Olostep")
    print("\nType 'exit' to quit.")

    while True:
        try:
            question = input(
                "\nEnter your research question: "
            ).strip()

            if question.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break

            if not question:
                print("Please enter a research question.")
                continue

            report = manager_agent(question)
            save_report(report)
            create_pdf_report(
    report,
    "research_report.pdf",
)

            print("\n" + "=" * 60)
            print("RESEARCH COMPLETED")
            print("=" * 60)
            print("\nReport saved as:")
            print(REPORT_FILE.resolve())

        except KeyboardInterrupt:
            print("\nResearch interrupted by user.")
            break

        except Exception as exc:
            print(f"\n[Error] {exc}")
            print(
                "Check that Ollama is running, the model is "
                "installed, and your .env API key is configured."
            )


if __name__ == "__main__":
    main()
