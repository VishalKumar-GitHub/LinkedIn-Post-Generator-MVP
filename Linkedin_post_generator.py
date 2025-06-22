import os
import time
import requests
import streamlit as st
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import random

# Load .env
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ---------- Utilities ----------

def get_trending_topic(domain):
    trends = {
        "AI": "ethical AI deployment",
        "Marketing": "hyper-personalization strategies",
        "Finance": "decentralized finance (DeFi)",
        "Tech": "edge computing and AI ops",
        "HR": "hybrid workforce culture",
        "Startups": "bootstrapped growth"
    }
    return trends.get(domain, "emerging innovation")

def detect_domains(posts):
    domains = ["AI", "Marketing", "Finance", "Tech", "HR", "Startups"]
    score = {d: sum(d.lower() in p.lower() for p in posts) for d in domains}
    return [d for d, v in sorted(score.items(), key=lambda x: -x[1]) if v > 0][:3]

def detect_tone(posts):
    text = " ".join(posts).lower()
    if any(w in text for w in ["fun", "journey", "team", "learned"]):
        return "Casual"
    if any(w in text for w in ["vision", "future", "empower"]):
        return "Inspirational"
    if any(w in text for w in ["framework", "results", "impact", "strategy"]):
        return "Professional"
    if any(w in text for w in ["pipeline", "automation", "system", "debug"]):
        return "Technical"
    return "Professional"  # default safe fallback

def scrape_profile(url):
    try:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(15)
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        bio = soup.find("div", class_="text-body-medium")
        posts = soup.find_all("span", class_="break-words")
        bio_text = bio.text.strip() if bio else "No bio found"
        post_texts = [p.text.strip() for p in posts if len(p.text.strip()) > 30][:5]
        return bio_text, post_texts
    except Exception as e:
        return f"Scraper error: {e}", []

def build_prompt(bio, posts, domain, tone, trend):
    keywords = ", ".join(set(" ".join(posts).split()[:20]))
    return (
        f"You are writing a LinkedIn post for a user whose bio is:\n{bio}\n\n"
        f"Their writing tone is {tone}, and they often write about {domain}.\n"
        f"Trending topic to include: {trend}.\n"
        f"Previous posts:\n{posts}\n"
        f"Popular keywords: {keywords}\n\n"
        f"Write a professional, structured LinkedIn post in the same tone. Start with a hook, include a value point, end with a call to action. Use relevant hashtags."
    )

def generate_post(prompt):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
    if res.status_code == 200:
        return res.json()['choices'][0]['message']['content'].strip()
    else:
        return f"API error: {res.status_code} - {res.text}"

# ---------- Streamlit UI ----------

st.set_page_config(page_title="LinkedIn Post Generator", layout="centered")
st.title("LinkedIn Post Generator (MVP)")
st.markdown("Paste your public LinkedIn profile link and generate a personalized post.")

linkedin_url = st.text_input("LinkedIn Profile URL")

if st.button("Analyze & Generate"):
    if linkedin_url:
        bio, posts = scrape_profile(linkedin_url)
        if posts:
            domain = detect_domains(posts)[0]
            tone = detect_tone(posts)
            trend = get_trending_topic(domain)
            prompt = build_prompt(bio, posts, domain, tone, trend)

            st.markdown(f"**Detected Tone**: `{tone}`  |  **Main Domain**: `{domain}`  |  **Trend**: `{trend}`")
            with st.spinner("Generating post..."):
                post = generate_post(prompt)
                st.session_state.generated_post = post
        else:
            st.error("Could not extract enough public posts from the profile.")

# ---------- Editable Output Section ----------
if "generated_post" in st.session_state:
    st.markdown("---")
    st.subheader("Your LinkedIn Post (Editable)")
    edited_post = st.text_area("Edit your post below", value=st.session_state.generated_post, height=300)

    # Copy to clipboard button
    st.markdown("""
        <button onclick="navigator.clipboard.writeText(document.getElementById('user_post').value)"
        style="padding:10px 20px; background-color:#007bff; border:none; color:white; border-radius:5px; cursor:pointer;">
        Copy to Clipboard
        </button>
        <textarea id="user_post" style="position:absolute;left:-9999px;">{}</textarea>
    """.format(edited_post.replace('"', '&quot;')), unsafe_allow_html=True)
