
import streamlit as st
from pathlib import Path

from main import manager_agent, save_report
from pdf_report import create_pdf_report


st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 Multi-Agent Research Assistant")
st.write(
    "Research topics using web search, multiple AI agents, "
    "local Ollama inference, and downloadable reports."
)

st.info("AI model: Local Ollama | Web search: Olostep")

question = st.text_area(
    "Enter your research question",
    placeholder=(
        "Example: How is agentic AI transforming healthcare, "
        "and what are its main benefits and risks?"
    ),
    height=120,
)

if st.button(
    "🚀 Start Research",
    type="primary",
    disabled=not question.strip(),
):
    try:
        with st.spinner(
            "Researching websites, analyzing evidence, "
            "reviewing findings, and generating reports..."
        ):
            report = manager_agent(question.strip())

            save_report(report)

            pdf_path = create_pdf_report(
                report,
                "research_report.pdf",
            )

            st.session_state["research_report"] = report
            st.session_state["research_question"] = question.strip()
            st.session_state["pdf_bytes"] = Path(pdf_path).read_bytes()

        st.success("Research completed! Your reports are ready.")

    except Exception as exc:
        st.error(f"Research failed: {exc}")
        st.exception(exc)


if "research_report" in st.session_state:
    st.divider()

    st.subheader("📄 Research Report")
    st.caption(
        f"Research question: {st.session_state['research_question']}"
    )

    markdown_report = st.session_state["research_report"]

    st.download_button(
        label="⬇️ Download Markdown Report",
        data=markdown_report,
        file_name="research_report.md",
        mime="text/markdown",
    )

    st.download_button(
        label="⬇️ Download PDF Report",
        data=st.session_state["pdf_bytes"],
        file_name="research_report.pdf",
        mime="application/pdf",
    )

    st.divider()
    st.markdown(markdown_report)
