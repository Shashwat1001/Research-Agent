import streamlit as st
from app.agent import answer

st.set_page_config(page_title="Agentic Research Assistant", layout="wide")

st.title("🔍 Agentic Research Assistant")
st.caption("Ask a complex, open-ended question. The assistant will research and summarize with citations.")

with st.form(key="research_form"):
    question = st.text_area("Enter your research question", height=120, placeholder="e.g., Compare the economic impacts of solar vs fossil fuels.")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        max_iters = st.number_input("Max Iterations", min_value=1, max_value=5, value=2)
    with col2:
        topk = st.number_input("Top Results/Query", min_value=2, max_value=10, value=6)
    with col3:
        model = st.text_input("LLM Model", value="gpt-4o-mini")
    with col4:
        safe_mode = st.checkbox("Safe Mode (no page fetch)", value=False)

    submit = st.form_submit_button("Run Research")

if submit and question.strip():
    with st.spinner("Researching..."):
        result = answer(
            question=question,
            max_iters=int(max_iters),
            topk=int(topk),
            model=model,
            safe_mode=safe_mode
        )

    st.subheader("Final Answer")
    st.write(result.get("answer",""))

    st.subheader("References")
    citations = result.get("citations", [])
    if citations:
        for c in citations:
            url = c.get("url","")
            title = c.get("title","(untitled)")
            sid = c.get("id","")
            st.markdown(f"- **[{sid}]** [{title}]({url})")
    else:
        st.write("No citations returned.")

    st.caption(f"Confidence: {result.get('confidence')}")
    if result.get("gaps"):
        st.warning("Gaps: " + "; ".join(result["gaps"]))
