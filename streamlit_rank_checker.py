import os
import glob
import streamlit as st
import pandas as pd
import io
import pdfplumber
import altair as alt

st.set_page_config(page_title="Rank Checker", page_icon="🏆", layout="centered")

# Initialize session state for form reset
if "last_selected_year" not in st.session_state:
    st.session_state.last_selected_year = None
if "sub01_input" not in st.session_state:
    st.session_state.sub01_input = ""
if "sub02_input" not in st.session_state:
    st.session_state.sub02_input = ""
if "show_result" not in st.session_state:
    st.session_state.show_result = False

# The app no longer hardcodes the dataset. It will load CSV/PDF files from user-selected
# year folders or from an uploaded file. This lets you place per-year files (e.g. `2021/`)
# under the project and select them at runtime.


def list_year_folders(path):
    """Return list of subfolders that contain CSV or PDF files (treated as years)."""
    years = []
    try:
        for entry in sorted(os.listdir(path)):
            full = os.path.join(path, entry)
            if os.path.isdir(full):
                # check for candidate files
                files = glob.glob(os.path.join(full, '*.csv')) + glob.glob(os.path.join(full, '*.pdf'))
                if files:
                    years.append(entry)
    except Exception:
        return []
    return years


def list_result_files(folder):
    files = glob.glob(os.path.join(folder, '*.csv')) + glob.glob(os.path.join(folder, '*.pdf'))
    return [os.path.basename(f) for f in sorted(files)]


st.title("🏆 Law Entrance Exam Rank Checker")
st.write("Select a year and enter your marks to check your rank.")

# Auto-scan current directory for year folders
current_dir = '.'
years = list_year_folders(current_dir)

if not years:
    st.warning("📁 No year folders with result files found in the current directory. Please create subfolders (e.g., `2021/`, `2022/`) with CSV/PDF result files.")
    st.stop()

st.markdown("---")
selected_year = st.selectbox("📅 Select Year", options=years, index=0)

# Reset form values when year changes
if selected_year != st.session_state.last_selected_year:
    st.session_state.last_selected_year = selected_year
    st.session_state.sub01_input = ""
    st.session_state.sub02_input = ""
    st.session_state.show_result = False


def parse_csv_buffer(buffer):
    try:
        # Try reading with different skip row strategies
        for skiprows in [0, 3, 4]:
            try:
                df = pd.read_csv(buffer, skiprows=skiprows)
                buffer.seek(0)  # Reset buffer for retry if needed
                
                # Skip empty rows
                df = df.dropna(how='all')
                
                # Map various column name variations to expected names
                column_mapping = {
                    'Serial No.': 'serial',
                    'Serial No': 'serial',
                    'serial': 'serial',
                    'Sub 01 Mark': 'sub01',
                    'Sub01 Mark': 'sub01',
                    'sub01': 'sub01',
                    'Sub 02 Mark': 'sub02',
                    'Sub02 Mark': 'sub02',
                    'sub02': 'sub02',
                    'Total Mark': 'total',
                    'Total': 'total',
                    'total': 'total',
                    'Merit Rank': 'rank',
                    'Rank': 'rank',
                    'rank': 'rank'
                }
                
                # Rename columns that match variations
                df = df.rename(columns={col: mapping for col, mapping in column_mapping.items() if col in df.columns})
                
                # Check if we have all required columns
                expected = {"serial", "sub01", "sub02", "total", "rank"}
                if expected.issubset(set(df.columns)):
                    # Keep only the required columns and convert to numeric
                    df = df[list(expected)].copy()
                    df['serial'] = pd.to_numeric(df['serial'], errors='coerce')
                    df['sub01'] = pd.to_numeric(df['sub01'], errors='coerce')
                    df['sub02'] = pd.to_numeric(df['sub02'], errors='coerce')
                    df['total'] = pd.to_numeric(df['total'], errors='coerce')
                    df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
                    df = df.dropna()
                    if len(df) > 0:
                        return df
            except Exception:
                continue
        
        return None
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        return None


def parse_pdf_file(file):
    try:
        with pdfplumber.open(file) as pdf:
            rows = []
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                for line in text.splitlines():
                    parts = [p for p in line.strip().split() if p]
                    nums = [p for p in parts if p.replace('.', '').replace('-', '').isdigit()]
                    if len(nums) >= 4:
                        candidate = nums[-5:]
                        if len(candidate) == 5:
                            try:
                                serial, s1, s2, total, rank = map(int, candidate)
                                rows.append((serial, s1, s2, total, rank))
                            except:
                                pass
            if rows:
                df = pd.DataFrame(rows, columns=["serial", "sub01", "sub02", "total", "rank"]).drop_duplicates()
                return df
            else:
                st.warning("Could not reliably parse candidate rows from PDF. Please try CSV or use built-in dataset.")
                return None
    except Exception as e:
        st.error(f"PDF parsing failed: {e}")
        return None


# -- Auto-load results file from selected year (silently) --
df_to_use = None

if selected_year:
    folder_path = os.path.join(current_dir, selected_year)
    files = list_result_files(folder_path)
    
    if files:
        # Auto-select the first file without showing selector
        chosen_file = files[0]
        fullpath = os.path.join(folder_path, chosen_file)
        
        if chosen_file.lower().endswith('.csv'):
            try:
                with open(fullpath, 'rb') as f:
                    df_to_use = parse_csv_buffer(f)
            except Exception as e:
                st.error(f"Failed loading CSV: {e}")
        elif chosen_file.lower().endswith('.pdf'):
            df_to_use = parse_pdf_file(fullpath)
    else:
        st.warning(f"No CSV/PDF files found in the `{selected_year}/` folder.")

if df_to_use is None:
    st.error("Could not load results file. Please ensure the year folder contains a valid CSV or PDF.")
    st.stop()

st.markdown("---")

# Input marks
st.markdown("---")
colA, colB = st.columns(2)
with colA:
    sub01 = st.text_input(
        "Sub 01 — General Knowledge",
        value=st.session_state.sub01_input,
        placeholder="Enter marks",
        key="sub01_input",
    )
with colB:
    sub02 = st.text_input(
        "Sub 02 — General Intelligence (IQ)",
        value=st.session_state.sub02_input,
        placeholder="Enter marks",
        key="sub02_input",
    )

check_button = st.button("Check Rank 🎉")

if check_button:
    st.session_state.show_result = True

if st.session_state.show_result:
    try:
        sub01_val = int(sub01)
        sub02_val = int(sub02)
        if sub01_val < 0 or sub02_val < 0 or sub01_val > 100 or sub02_val > 100:
            raise ValueError("Marks must be between 0 and 100")
        if sub01 == "" or sub02 == "":
            raise ValueError("Please enter both marks")

        total = sub01_val + sub02_val
        better = df_to_use[df_to_use['total'] > total]
        worse = df_to_use[df_to_use['total'] < total]

        better_sub01 = df_to_use[df_to_use['sub01'] > sub01_val]
        better_sub02 = df_to_use[df_to_use['sub02'] > sub02_val]

        if len(df_to_use) == 0:
            raise ValueError("No candidate data found in the selected year file.")

        rank = 1 if better.empty else len(better) + 1
        rank_sub01 = 1 if better_sub01.empty else len(better_sub01) + 1
        rank_sub02 = 1 if better_sub02.empty else len(better_sub02) + 1

        percentile = round(len(worse) / len(df_to_use) * 100, 1)

        st.markdown(
            f"<div style='text-align:center;'>\n<h1 style='font-size:84px;margin:0;'>Rank {rank}</h1>\n<p style='margin:6px;color:#444;'>Total: <strong>{total}</strong> — You beat <strong>{percentile}%</strong> of candidates</p>\n</div>",
            unsafe_allow_html=True,
        )

        if rank == 1:
            st.snow()
            st.balloons()
            st.success("🌟 Incredible — TOPPER! 🌟")
        elif rank <= 10:
            st.balloons()
            st.success(f"Amazing — top {rank}! 🎉")
        elif rank <= 50:
            st.success("Great — inside top 50! ✨")
        else:
            st.info("Keep going — you can improve more!")

        st.markdown("**Percentile**")
        pct_col = pd.DataFrame({"pct": [percentile]})
        chart = alt.Chart(pct_col).mark_bar(color="#667eea").encode(
            x=alt.X("pct:Q", scale=alt.Scale(domain=[0, 100]))
        ).properties(height=40)
        st.altair_chart(chart, use_container_width=True)

        subject1_label = "General Knowledge"
        subject2_label = "General Intelligence (IQ)"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Marks", total)
        c2.metric(f"{subject1_label} Rank", rank_sub01)
        c3.metric(f"{subject2_label} Rank", rank_sub02)
        c4.metric("Percentile", f"{percentile}%")

        st.markdown("**Score distribution (Total marks)**")
        hist = alt.Chart(df_to_use).mark_bar().encode(
            alt.X("total:Q", bin=alt.Bin(maxbins=25), title="Total marks"),
            y="count()",
        ).properties(height=200)
        st.altair_chart(hist, use_container_width=True)

        neighbors = df_to_use.copy()
        neighbors["diff"] = (neighbors["total"] - total).abs()
        neighbors = neighbors.sort_values(["diff", "serial"]).head(8)
        st.markdown("**Closest candidates**")
        neighbors = neighbors.rename(columns={
            "sub01": "General Knowledge",
            "sub02": "General Intelligence (IQ)",
        })
        st.table(neighbors[["serial", "General Knowledge", "General Intelligence (IQ)", "total", "rank"]].reset_index(drop=True))

        st.markdown("---")
        st.success("Keep shining — every rank is progress, and you're doing great! 🌟")
        st.write("Cheer on every step: strong effort, focused practice, and confidence will keep the momentum going.")
    except ValueError as e:
        st.error(str(e))
        st.session_state.show_result = False

