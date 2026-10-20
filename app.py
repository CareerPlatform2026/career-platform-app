import hashlib, os, sqlite3
from pathlib import Path
from datetime import datetime
import streamlit as st

st.set_page_config(page_title="Career Platform", page_icon="🎓", layout="wide")
DB = Path(__file__).resolve().parent / "career_platform_complete.db"

def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def pw_hash(p):
    return hashlib.sha256(p.encode()).hexdigest()

def init():
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
            degree TEXT DEFAULT '', skills TEXT DEFAULT '', interests TEXT DEFAULT '',
            created_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS jobs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, company TEXT NOT NULL,
            location TEXT DEFAULT '', required_skills TEXT DEFAULT '', description TEXT DEFAULT '',
            created_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS applications(
            id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, job_id INTEGER NOT NULL,
            applied_at TEXT NOT NULL, UNIQUE(student_id,job_id))""")

def student(sid):
    with connect() as c:
        return c.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone()

CAREERS = {
"Data Analyst": {"keywords":["data","numbers","business","research"],"required":["Excel","SQL","Data visualization","Basic statistics"],"later":["Python","Power BI or Tableau","Portfolio projects"],"low":["Advanced deep learning","Learning many languages at once"],"project":"Analyse sample sales data and make a dashboard.","outlook":"Useful across many industries; practical projects and communication matter."},
"Software Developer": {"keywords":["coding","apps","websites","technology","problem solving"],"required":["One programming language","Git basics","Problem solving","Basic databases"],"later":["Web development","APIs","Testing","Cloud basics"],"low":["Many languages at once","Advanced cloud architecture before basics"],"project":"Build a small task tracker or portfolio website.","outlook":"Opportunities span web, mobile, and product teams; projects and coding ability matter."},
"AI / Machine Learning": {"keywords":["ai","automation","data","math","technology"],"required":["Python basics","Basic statistics","Data handling"],"later":["Machine learning concepts","Model evaluation","Responsible AI","Projects"],"low":["Advanced deep learning before fundamentals","Certificates without projects"],"project":"Build a simple prediction demo and explain its limits.","outlook":"AI work is growing, but strong fundamentals and demonstrable projects are important."},
"Cybersecurity": {"keywords":["security","networks","investigation","privacy","technology"],"required":["Networking basics","Linux basics","Security fundamentals"],"later":["Scripting","Log analysis","Cloud security","Practice labs"],"low":["Advanced exploit development before basics","Practising without permission"],"project":"Keep a learning journal from a legal practice lab.","outlook":"Security skills are needed across sectors; foundations and ethical practice matter."},
"UI/UX Designer": {"keywords":["design","creativity","people","apps","visuals"],"required":["Design principles","Wireframing","User research basics"],"later":["Figma","Prototyping","Accessibility","Portfolio case studies"],"low":["Many tools at once","Advanced animation before basics"],"project":"Redesign one app screen and explain the user problem.","outlook":"Portfolio quality and clear design decisions help in product teams."},
"Digital Marketing": {"keywords":["marketing","content","social media","business","creativity"],"required":["Content writing","Marketing fundamentals","Basic analytics"],"later":["SEO","Campaign tools","Ad platforms","Conversion tracking"],"low":["Every ad platform at once","Advanced automation before basics"],"project":"Create a content calendar with success measures.","outlook":"Roles exist in agencies, startups, and in-house teams; results and communication matter."},
"HR / Talent Acquisition": {"keywords":["people","communication","organising","teamwork","business"],"required":["Communication","Interview coordination","Spreadsheet basics"],"later":["Recruitment tools","Sourcing","HR fundamentals","Reporting"],"low":["Advanced analytics before spreadsheet basics","Many systems before fundamentals"],"project":"Create a sample interview schedule using fictional data.","outlook":"Organisation, communication, and confidentiality are valuable."},
"Business / Operations Analyst": {"keywords":["business","planning","numbers","process","problem solving"],"required":["Excel","Communication","Process mapping"],"later":["SQL","Dashboarding","Documentation","Project coordination"],"low":["Machine learning before Excel basics","Many dashboard tools at once"],"project":"Map a simple process and suggest measurable improvements.","outlook":"These roles improve business processes; analytical thinking and industry knowledge help."}
}

def split_items(s):
    return [x.strip() for x in (s or "").replace(";", ",").split(",") if x.strip()]

def recommend(degree, interests):
    txt = (interests or "").lower()
    ranked = sorted(((sum(2 for k in v["keywords"] if k in txt), name) for name,v in CAREERS.items()), reverse=True)
    result = [name for score,name in ranked if score > 0][:3]
    return result or ["Data Analyst", "Business / Operations Analyst", "Digital Marketing"]

init()
if "student_id" not in st.session_state: st.session_state.student_id = None
if "is_admin" not in st.session_state: st.session_state.is_admin = False

st.sidebar.title("🎓 Career Platform")
if st.session_state.student_id:
    s = student(st.session_state.student_id)
    menu = st.sidebar.radio("Menu", ["Dashboard","Browse Jobs","My Applications","My Profile","AI Career Prediction"])
    if st.sidebar.button("Log out"):
        st.session_state.student_id = None
        st.rerun()
elif st.session_state.is_admin:
    menu = st.sidebar.radio("Admin Menu", ["Admin Dashboard","Manage Jobs","Students","Applications"])
    if st.sidebar.button("Admin log out"):
        st.session_state.is_admin = False
        st.rerun()
else:
    menu = st.sidebar.radio("Menu", ["Home","Student Registration","Student Login","Admin Login"])

if menu == "Home":
    st.title("🎓 Career Platform")
    st.write("Explore jobs, manage applications, and plan your career skills.")
    st.info("Register or sign in using the sidebar.")

elif menu == "Student Registration":
    st.title("Student Registration")
    with st.form("register"):
        name=st.text_input("Full name")
        email=st.text_input("Email").strip().lower()
        password=st.text_input("Password", type="password")
        degree=st.selectbox("Degree",["","B.Com","BBA","BCA","B.Sc","B.E","B.Tech","BA","B.Des","BFA","Other"])
        ok=st.form_submit_button("Create account")
    if ok:
        if not name.strip() or not email or not password: st.error("Fill name, email, and password.")
        else:
            try:
                with connect() as c:
                    c.execute("INSERT INTO students(name,email,password_hash,degree,created_at) VALUES(?,?,?,?,?)",
                              (name.strip(),email,pw_hash(password),degree,datetime.now().isoformat(timespec="seconds")))
                st.success("Account created. Go to Student Login.")
            except sqlite3.IntegrityError: st.error("Email already registered.")

elif menu == "Student Login":
    st.title("Student Login")
    email=st.text_input("Email",key="login_email").strip().lower()
    password=st.text_input("Password",type="password",key="login_password")
    if st.button("Login"):
        with connect() as c: s=c.execute("SELECT * FROM students WHERE email=?",(email,)).fetchone()
        if s and s["password_hash"] == pw_hash(password):
            st.session_state.student_id=s["id"]; st.rerun()
        else: st.error("Incorrect email or password.")

elif menu == "Admin Login":
    st.title("Admin Login")
    password = st.text_input("Admin password", type="password")

    try:
        configured = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        configured = os.environ.get("ADMIN_PASSWORD", "")

    if st.button("Login as admin"):
        if configured and password == configured:
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.error(
                "Admin password configure pannala or password incorrect. "
                "Check .streamlit/secrets.toml."
            )
elif menu == "Dashboard":
    s=student(st.session_state.student_id)
    st.title(f"Welcome, {s['name']} 👋")
    with connect() as c:
        jobs=c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        apps=c.execute("SELECT COUNT(*) FROM applications WHERE student_id=?",(s["id"],)).fetchone()[0]
    a,b,d=st.columns(3); a.metric("Available jobs",jobs); b.metric("Your applications",apps); d.metric("Degree",s["degree"] or "Not set")
    st.write("Use the menu to browse jobs, update your profile, or get career recommendations.")

elif menu == "My Profile":
    s=student(st.session_state.student_id)
    st.title("My Profile")
    with st.form("profile"):
        name=st.text_input("Full name",s["name"])
        opts=["","B.Com","BBA","BCA","B.Sc","B.E","B.Tech","BA","B.Des","BFA","Other"]
        deg=s["degree"] if s["degree"] in opts else "Other"
        degree=st.selectbox("Degree",opts,index=opts.index(deg))
        skills=st.text_area("Skills (comma separated; blank is okay)",s["skills"] or "")
        interests=st.text_area("Interests (e.g. business, design, coding, people, data)",s["interests"] or "")
        save=st.form_submit_button("Save profile")
    if save:
        with connect() as c: c.execute("UPDATE students SET name=?,degree=?,skills=?,interests=? WHERE id=?",(name.strip(),degree,skills.strip(),interests.strip(),s["id"]))
        st.success("Profile saved.")

elif menu == "AI Career Prediction":
    s=student(st.session_state.student_id)
    st.title("🧭 Career Prediction & Skill Gap Analysis")
    st.write("Skills can be blank. This is rule-based guidance, not a trained AI model.")
    with st.form("career"):
        opts=["","B.Com","BBA","BCA","B.Sc","B.E","B.Tech","BA","B.Des","BFA","Other","Any degree"]
        deg=s["degree"] if s["degree"] in opts else "Other"
        degree=st.selectbox("Your degree",opts,index=opts.index(deg))
        interests=st.text_input("Interests (optional)",s["interests"] or "",placeholder="business, data, design, people, coding")
        skills=st.text_input("Skills you already know (optional)",s["skills"] or "",placeholder="Leave blank if beginner")
        go=st.form_submit_button("Predict careers")
    if go:
        with connect() as c: c.execute("UPDATE students SET degree=?,interests=?,skills=? WHERE id=?",(degree,interests,skills,s["id"]))
        known={x.lower() for x in split_items(skills)}
        st.subheader("Suggested career paths")
        for i,career in enumerate(recommend(degree,interests),1):
            info=CAREERS[career]
            missing=[x for x in info["required"] if x.lower() not in known]
            with st.expander(f"{i}. {career}",expanded=(i==1)):
                st.write("A starting option based on the interests you entered; try a project before deciding.")
                st.markdown("**Skill gap — skills to learn**")
                st.write(", ".join(missing) if missing else "You listed the beginner skills. Practise them in projects.")
                matched=[x for x in info["required"] if x.lower() in known]
                st.markdown("**Skills you already listed**")
                st.write(", ".join(matched) if matched else "No matching skills entered yet — that's okay for beginners.")
                st.markdown("**Low priority for now**"); st.write(", ".join(info["low"]))
                st.markdown("**Learning roadmap**")
                roadmap=missing+[x for x in info["later"] if x.lower() not in known]
                for n,item in enumerate(roadmap or ["Build a portfolio project","Practise interview questions"],1): st.write(f"{n}. {item}")
                st.markdown("**First project**"); st.write(info["project"])
                st.markdown("**Future career outlook**"); st.write(info["outlook"])
        st.success("Done. These suggestions are guidance, not a job guarantee.")

elif menu == "Browse Jobs":
    st.title("Browse Jobs")
    with connect() as c: jobs=c.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
    if not jobs: st.info("No jobs listed yet. Admin can add jobs after login.")
    for job in jobs:
        with st.expander(f"{job['title']} — {job['company']}"):
            st.write(f"Location: {job['location'] or 'Not specified'}")
            st.write(job["description"] or "No description")
            st.write("Required skills: "+(job["required_skills"] or "Not specified"))
            if st.button("Apply",key=f"apply{job['id']}"):
                try:
                    with connect() as c: c.execute("INSERT INTO applications(student_id,job_id,applied_at) VALUES(?,?,?)",(st.session_state.student_id,job["id"],datetime.now().isoformat(timespec="seconds")))
                    st.success("Application submitted.")
                except sqlite3.IntegrityError: st.warning("Already applied.")

elif menu == "My Applications":
    st.title("My Applications")
    with connect() as c:
        rows=c.execute("SELECT jobs.title,jobs.company,applications.applied_at FROM applications JOIN jobs ON jobs.id=applications.job_id WHERE applications.student_id=? ORDER BY applications.id DESC",(st.session_state.student_id,)).fetchall()
    if rows:
        for r in rows: st.write(f"**{r['title']}** — {r['company']} · {r['applied_at'][:10]}")
    else: st.info("No applications yet.")

elif menu == "Admin Dashboard":
    st.title("Admin Dashboard")
    with connect() as c:
        a=c.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        b=c.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        d=c.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    x,y,z=st.columns(3); x.metric("Students",a); y.metric("Jobs",b); z.metric("Applications",d)

elif menu == "Manage Jobs":
    st.title("Manage Jobs")
    with st.form("job"):
        title=st.text_input("Job title"); company=st.text_input("Company"); location=st.text_input("Location")
        required=st.text_input("Required skills (comma separated)"); desc=st.text_area("Description")
        add=st.form_submit_button("Add job")
    if add:
        if not title.strip() or not company.strip(): st.error("Job title and company required.")
        else:
            with connect() as c: c.execute("INSERT INTO jobs(title,company,location,required_skills,description,created_at) VALUES(?,?,?,?,?,?)",(title.strip(),company.strip(),location.strip(),required.strip(),desc.strip(),datetime.now().isoformat(timespec="seconds")))
            st.success("Job added.")
    with connect() as c: jobs=c.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
    for j in jobs:
        st.write(f"**{j['title']}** — {j['company']}")
        if st.button("Delete job",key=f"del{j['id']}"):
            with connect() as c: c.execute("DELETE FROM applications WHERE job_id=?",(j["id"],)); c.execute("DELETE FROM jobs WHERE id=?",(j["id"],))
            st.rerun()

elif menu == "Students":
    st.title("Students")
    with connect() as c: rows=c.execute("SELECT id,name,email,degree,skills,interests,created_at FROM students ORDER BY id DESC").fetchall()
    st.dataframe([dict(r) for r in rows],use_container_width=True)

elif menu == "Applications":
    st.title("Applications")
    with connect() as c:
        rows=c.execute("SELECT applications.id,students.name,students.email,jobs.title,jobs.company,applications.applied_at FROM applications JOIN students ON students.id=applications.student_id JOIN jobs ON jobs.id=applications.job_id ORDER BY applications.id DESC").fetchall()
    st.dataframe([dict(r) for r in rows],use_container_width=True)
