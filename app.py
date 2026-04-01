import streamlit as st
import requests
import base64
import concurrent.futures
from litellm import completion

# 1. CONFIGURATION & CUSTOM CSS UI
st.set_page_config(page_title="Inspectra | Multi-Agent Review", page_icon="⚡", layout="wide")

st.markdown("""
    <style>
    /* Hide Streamlit Default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Style the main title */
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: -webkit-linear-gradient(45deg, #0072ff, #00c6ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #6c757d;
        margin-bottom: 2rem;
    }
    /* Style the tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 4px 4px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">⚡ Inspectra</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Enterprise-grade code analysis powered by a Mixture of Experts (MoE) AI architecture.</p>', unsafe_allow_html=True)

# 2. GITHUB FETCHER LOGIC
def parse_github_url(url):
    parts = url.rstrip('/').split('/')
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    return None, None

def fetch_repo_contents(owner, repo, token=None, max_files=15):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
        
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    repo_res = requests.get(repo_url, headers=headers)
    
    if repo_res.status_code == 401:
        return None, " Unauthorized: Your GitHub Token is invalid or expired.", 0
    if repo_res.status_code == 403:
        return None, " GitHub API Rate Limit exceeded! Please add a valid GitHub Token.", 0
    if repo_res.status_code == 404:
        return None, " Repository not found. It might be private, or the URL is incorrect.", 0
    if repo_res.status_code != 200:
        return None, f"Failed to fetch repository info. (Status Code: {repo_res.status_code})", 0
        
    default_branch = repo_res.json().get("default_branch", "main")
    
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
    tree_res = requests.get(tree_url, headers=headers)
        
    if tree_res.status_code != 200:
        return None, f"Failed to fetch tree for branch '{default_branch}'.", 0

    tree = tree_res.json().get("tree", [])
    valid_extensions = ('.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.cpp', '.c', '.h', '.cs', '.rb', '.php')
    source_files = [item for item in tree if item["path"].endswith(valid_extensions)]
    
    source_files = source_files[:max_files]
    file_count = len(source_files)
    
    repo_data = ""
    for item in source_files:
        if item["type"] == "blob":
            blob_url = item["url"]
            blob_res = requests.get(blob_url, headers=headers)
            
            if blob_res.status_code == 403:
                return None, " Hit GitHub Rate Limit while fetching files. Add a GitHub token!", 0
                
            blob_json = blob_res.json()
            if "content" in blob_json:
                content = base64.b64decode(blob_json["content"]).decode('utf-8', errors='ignore')
                repo_data += f"\n\n--- FILE: {item['path']} ---\n\n{content}"
            
    return repo_data, None, file_count

# 3. MULTI-AGENT LLM LOGIC
def agent_review(model_name, api_key, role_prompt, code_context):
    try:
        response = completion(
            model=model_name,
            api_key=api_key,
            messages=[
                {"role": "system", "content": role_prompt},
                {"role": "user", "content": f"Review the following repository code:\n\n{code_context}"}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error with model {model_name}: {str(e)}"

def synthesize_reviews(model_name, api_key, arch_review, sec_review, perf_review, qa_review):
    synthesis_prompt = """
    You are the Lead Principal Engineer. You have received four specialized code review reports from your top engineers:
    1. Architectural Review
    2. Security Review
    3. Performance Review
    4. QA & Testing Review
    
    Your job is to synthesize these into a single, cohesive, highly professional Markdown report.
    Structure the report with:
    - Executive Summary
    - Critical Vulnerabilities (if any)
    - Architecture & Design Feedback
    - Performance Optimization Opportunities
    - QA & Testing Strategy
    - Actionable Next Steps
    
    Do not mention the "agents" or "models". Present this as a unified review from 'OmniCode'.
    """
    
    combined_content = f"### Architecture Review\n{arch_review}\n\n### Security Review\n{sec_review}\n\n### Performance Review\n{perf_review}\n\n### QA Review\n{qa_review}"
    
    try:
        response = completion(
            model=model_name,
            api_key=api_key,
            messages=[
                {"role": "system", "content": synthesis_prompt},
                {"role": "user", "content": combined_content}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during synthesis: {str(e)}"

# 4. UI SIDEBAR & SMART ROUTING
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/source-code.png", width=60)
    st.title(" Settings")
    st.markdown("Automated code reviews leveraging parallel AI agents.")
    
    with st.expander("⚙️ Pro Mode (Custom API Keys)", expanded=False):
        st.caption("Override default open models with your proprietary keys.")
        user_openai_key = st.text_input("OpenAI Key", type="password")
        user_anthropic_key = st.text_input("Anthropic Key", type="password")
        user_gemini_key = st.text_input("Gemini Pro Key", type="password")
        
    with st.expander("🔐 GitHub Authentication", expanded=False):
        st.caption("Required for private repos or high rate limits.")
        user_github_token = st.text_input("GitHub Token", type="password")

def get_model_config(role):
    default_groq = st.secrets.get("GROQ_API_KEY", "")
    default_gemini = st.secrets.get("GEMINI_API_KEY", "")
    
    if role == "architect" or role == "lead" or role == "qa":
        if user_openai_key:
            return "gpt-4o", user_openai_key
        return "groq/llama-3.1-8b-instant", default_groq
        
    elif role == "auditor":
        if user_anthropic_key:
            return "claude-3-5-sonnet-20240620", user_anthropic_key
        return "groq/llama-3.3-70b-versatile", default_groq

    elif role == "optimizer":
        if user_gemini_key:
            return "gemini/gemini-1.5-pro", user_gemini_key
        return "gemini/gemini-1.5-flash", default_gemini

# 5. MAIN EXECUTION



# Use a cleaner layout for the input
col_input, col_btn = st.columns([4, 1])
with col_input:
    repo_url = st.text_input("🔗 Target GitHub Repository", placeholder="https://github.com/owner/repo", label_visibility="collapsed")
with col_btn:
    run_button = st.button("🚀 Analyze Repo", type="primary", use_container_width=True)

if run_button:
    if not repo_url:
        st.error("⚠️ Please enter a GitHub URL to begin.", icon="🚨")
        st.stop()
        
    owner, repo = parse_github_url(repo_url)
    if not owner or not repo:
        st.error("⚠️ Invalid GitHub URL format.", icon="🚨")
        st.stop()
        
    active_gh_token = user_github_token if user_github_token else st.secrets.get("GITHUB_TOKEN", None)

    with st.status("Initializing OmniCode Pipeline...", expanded=True) as status:
        st.write("📥 Fetching code from repository...")
        code_data, err, file_count = fetch_repo_contents(owner, repo, active_gh_token)
        
        if err:
            status.update(label="Pipeline Failed", state="error")
            st.error(err, icon="🚨")
            st.stop()
            
        if not code_data:
            status.update(label="No source code found", state="error")
            st.warning("Make sure the repository contains standard source code files.", icon="⚠️")
            st.stop()
            
        # Determine Models
        arch_model, arch_key = get_model_config("architect")
        sec_model, sec_key = get_model_config("auditor")
        perf_model, perf_key = get_model_config("optimizer")
        qa_model, qa_key = get_model_config("qa")
        lead_model, lead_key = get_model_config("lead")
        
        st.write(f"✅ Fetched **{file_count}** source files. Deploying AI agents...")
        
        # Agent Prompts
        arch_prompt = "You are a Software Architect. Focus exclusively on design patterns, SOLID principles, code structure, modularity, and maintainability. Provide your review in Markdown."
        sec_prompt = "You are a Security Researcher. Focus exclusively on finding security vulnerabilities, injection risks, unsafe data handling, and authorization flaws. Be specific. Markdown only."
        perf_prompt = "You are a Performance Engineer. Focus exclusively on algorithmic efficiency, memory leaks, unnecessary rendering/loops, and micro-optimizations. Markdown only."
        qa_prompt = "You are a QA Automation Engineer. Focus exclusively on finding edge cases, missing error handling, and recommending specific unit test structures. Markdown only."
        
        # Run Agents in Parallel
        status.update(label="Executing parallel MoE analysis...", state="running")
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_arch = executor.submit(agent_review, arch_model, arch_key, arch_prompt, code_data)
            future_sec = executor.submit(agent_review, sec_model, sec_key, sec_prompt, code_data)
            future_perf = executor.submit(agent_review, perf_model, perf_key, perf_prompt, code_data)
            future_qa = executor.submit(agent_review, qa_model, qa_key, qa_prompt, code_data)
            
            arch_result = future_arch.result()
            sec_result = future_sec.result()
            perf_result = future_perf.result()
            qa_result = future_qa.result()
            
        st.write("✅ Agent analysis complete. Synthesizing insights...")
        status.update(label=f"Generating executive report via {lead_model}...", state="running")
        
        # Synthesize (Now includes QA!)
        final_report = synthesize_reviews(lead_model, lead_key, arch_result, sec_result, perf_result, qa_result)
        status.update(label="Analysis Successfully Completed!", state="complete")

    # Metrics Dashboard
    m1, m2, m3 = st.columns(3)
    m1.metric(label="Files Analyzed", value=file_count)
    m2.metric(label="Agents Deployed", value="4 Experts")
    m3.metric(label="Lead Synthesizer", value=lead_model.split('/')[-1])
    
    st.divider()
    
    # Header & Export
    c1, c2 = st.columns([3, 1])
    with c1:
        st.subheader("📑 Final Diagnostic Report")
    with c2:
        st.download_button(
            label="📥 Download Markdown",
            data=final_report,
            file_name=f"{repo}_omnicode_audit.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    # UI Tabs for viewing
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Executive Synthesis", "🏗️ Architect", "🔒 Security", "⚡ Performance", "🧪 QA Engineer"])
    
    with tab1:
        st.markdown(final_report)
    with tab2:
        st.caption(f"**Engine:** `{arch_model}`")
        st.markdown(arch_result)
    with tab3:
        st.caption(f"**Engine:** `{sec_model}`")
        st.markdown(sec_result)
    with tab4:
        st.caption(f"**Engine:** `{perf_model}`")
        st.markdown(perf_result)
    with tab5:
        st.caption(f"**Engine:** `{qa_model}`")
        st.markdown(qa_result)