import os
import streamlit as st
import pickle
import pandas as pd
import requests
import time

from io import BytesIO

similarity_url = "https://drive.google.com/uc?export=download&id=1YLqOgAB8UhARod3pJA9ZTohA8xRbNx2E"

@st.cache_data(show_spinner=True)
def load_similarity(url):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    return pickle.load(BytesIO(response.content))

similarity = load_similarity(similarity_url)

#similarity = pickle.load(BytesIO(response.content))

# ====== Load Data ======
movies_dict = pickle.load(open('movie_dict.pkl','rb'))
movies = pd.DataFrame(movies_dict)
#similarity = pickle.load(open('similarity.pkl','rb'))

# ====== TMDB Poster Fetch with Safe Fallback ======
def fetch_poster(movie_id, retries=3):
    api_key = os.getenv("TMDB_API_KEY")
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            poster_path = data.get('poster_path')
            if poster_path:
                return "https://image.tmdb.org/t/p/w500" + poster_path
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt+1} failed for movie_id {movie_id}: {e}")
            time.sleep(0.5)  # wait before retrying
    
    # fallback placeholder
    return "https://via.placeholder.com/300x450?text=No+Image"

# ====== Recommendation Function ======
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_posters = []

    for i in movie_list:
        movie_idx = i[0]
        title = movies.iloc[movie_idx].title
        movie_id = movies.iloc[movie_idx].movie_id

        recommended_movies.append(title)

        # Safe poster fetch
        poster = fetch_poster(movie_id)
        if not poster:
            poster = "https://via.placeholder.com/300x450?text=No+Image"
        recommended_posters.append(poster)

        # small delay to avoid TMDB blocking
        time.sleep(0.2)

    # Ensure lists are always length 5
    while len(recommended_movies) < 5:
        recommended_movies.append("No Movie")
        recommended_posters.append("https://via.placeholder.com/300x450?text=No+Image")

    return recommended_movies, recommended_posters

# ====== Streamlit Layout ======
st.set_page_config(layout="wide")

# Header
left, center, right = st.columns([1,2,1])
with center:
    st.title("🎬 Movie Recommender System")
    st.write("Select a movie and get similar recommendations.")

    selected_movie = st.selectbox("Choose a movie", movies['title'].values)
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        recommend_btn = st.button("Recommend")

# Show Recommendations
if recommend_btn:
    recommended_movies, recommended_posters = recommend(selected_movie)

    st.markdown("<h2 style='text-align:center;'>Recommended Movies</h2>", unsafe_allow_html=True)

    cols = st.columns(5, gap="large")
    for i, col in enumerate(cols):
        with col:
            st.image(recommended_posters[i])
            st.caption(recommended_movies[i])

st.markdown("---")
st.caption("AI Movie Recommendation Project")


