import os
import streamlit as st
from supabase import create_client, Client

# =========================================
# PAGE CONFIG
# =========================================

st.set_page_config(
    page_title="Startup CFO Challenge",
    page_icon="💰",
    layout="wide"
)


# =========================================
# SUPABASE CONNECTION
# =========================================

def get_supabase():

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]

    return create_client(url, key)


# =========================================
# HELPER FUNCTIONS
# =========================================

def pv_cash_flows(cash_flows, rate):

    return sum(
        cash_flow / ((1 + rate) ** year)
        for year, cash_flow in enumerate(
            cash_flows,
            start=1
        )
    )


def count_votes(submissions, option):

    return sum(
        1
        for submission in submissions
        if submission["decision"] == option
    )


# =========================================
# INSTRUCTOR PAGE
# =========================================

def instructor_page():

    # =====================================
    # INSTRUCTOR LOGIN
    # =====================================

    if "instructor_authenticated" not in st.session_state:
        st.session_state.instructor_authenticated = False

    if not st.session_state.instructor_authenticated:

        st.title("🔐 Instructor Dashboard")

        st.write(
            "Enter the instructor password to access the game controls."
        )

        instructor_password = st.text_input(
            "Instructor Password",
            type="password"
        )

        if st.button(
            "Login",
            type="primary"
        ):

            admin_password = os.getenv("ADMIN_PASSWORD")

            if not admin_password:
                admin_password = st.secrets["admin"]["password"]

            if instructor_password == admin_password:

                st.session_state.instructor_authenticated = True

                st.rerun()

            else:

                st.error(
                    "Incorrect password."
                )

        return

    supabase: Client = get_supabase()

    # =====================================
    # READ GAME STATE
    # =====================================

    state_response = (
        supabase
        .table("game_state")
        .select("*")
        .eq("id", 1)
        .execute()
    )

    if not state_response.data:

        st.error(
            "Game state not found."
        )

        return


    game_state = state_response.data[0]

    current_round = game_state["current_round"]
    round_status = game_state["round_status"]


    # =====================================
    # READ TEAMS
    # =====================================

    teams_response = (
        supabase
        .table("teams")
        .select(
            "id, teamname, cash, debt, ev"
        )
        .order("id")
        .execute()
    )

    teams = teams_response.data


    # =====================================
    # READ CURRENT ROUND SUBMISSIONS
    # =====================================

    submissions_response = (
        supabase
        .table("submissions")
        .select("*")
        .eq("round", current_round)
        .execute()
    )

    submissions = submissions_response.data


    submissions_by_team = {
        submission["team_id"]: submission
        for submission in submissions
    }


    submitted_count = len(
        submissions_by_team
    )

    waiting_count = (
        len(teams)
        - submitted_count
    )


    # =====================================
    # CORRECT ANSWERS
    # =====================================

    correct_answers = {
        1: "B",
        2: "C",
        3: "C",
        4: "B",
        5: "A",
        6: "B"
    }


    # =====================================
    # HEADER
    # =====================================

    st.title(
        "💰 Startup CFO Challenge"
    )

    st.caption(
        "Instructor Control Centre"
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Round",
            current_round
        )


    with col2:

        st.metric(
            "Submitted",
            f"{submitted_count} / {len(teams)}"
        )


    with col3:

        st.metric(
            "Waiting",
            waiting_count
        )


    with col4:

        if round_status == "open":

            st.metric(
                "Status",
                "🟢 OPEN"
            )

        elif round_status == "locked":

            st.metric(
                "Status",
                "🔒 LOCKED"
            )

        elif round_status == "revealed":

            st.metric(
                "Status",
                "👁 REVEALED"
            )


    if teams:

        st.progress(
            submitted_count
            / len(teams)
        )


    st.divider()


    # =====================================
    # ROUND CONTROLS
    # =====================================

    st.subheader(
        "🎛️ Round Controls"
    )


    control1, control2, control3, control4 = st.columns(4)


    # -------------------------------------
    # OPEN ROUND
    # -------------------------------------

    with control1:

        if st.button(
            "🟢 Open Round",
            width="stretch"
        ):

            (
                supabase
                .table("game_state")
                .update({
                    "round_status": "open"
                })
                .eq("id", 1)
                .execute()
            )

            st.rerun()


    # -------------------------------------
    # LOCK ROUND
    # -------------------------------------

    with control2:

        if st.button(
            "🔒 Lock Round",
            width="stretch"
        ):

            (
                supabase
                .table("game_state")
                .update({
                    "round_status": "locked"
                })
                .eq("id", 1)
                .execute()
            )

            st.rerun()


    # -------------------------------------
    # REVEAL
    # -------------------------------------

    with control3:

        if st.button(
            "👁 Reveal Results",
            width="stretch"
        ):

            (
                supabase
                .table("game_state")
                .update({
                    "round_status": "revealed"
                })
                .eq("id", 1)
                .execute()
            )

            st.rerun()


    # -------------------------------------
    # REFRESH
    # -------------------------------------

    with control4:

        if st.button(
            "🔄 Refresh",
            width="stretch"
        ):

            st.rerun()


    # =====================================
    # STATUS MESSAGE
    # =====================================

    if round_status == "open":

        st.success(
            "🟢 Round is OPEN — teams can submit their decisions."
        )

    elif round_status == "locked":

        st.warning(
            "🔒 Round is LOCKED — teams can no longer submit."
        )

    elif round_status == "revealed":

        st.info(
            "👁 Results are REVEALED."
        )


    st.divider()


    # =====================================
    # ROUND NAVIGATION
    # =====================================

    st.subheader(
        "🧭 Round Navigation"
    )


    nav1, nav2, nav3 = st.columns(
        [1, 2, 1]
    )


    # -------------------------------------
    # PREVIOUS ROUND
    # -------------------------------------

    with nav1:

        if st.button(
            "⬅️ Previous Round",
            width="stretch",
            disabled=current_round <= 1
        ):

            (
                supabase
                .table("game_state")
                .update({
                    "current_round":
                        current_round - 1,

                    "round_status":
                        "open"
                })
                .eq("id", 1)
                .execute()
            )

            st.rerun()


    # -------------------------------------
    # JUMP TO ROUND
    # -------------------------------------

    with nav2:

        selected_round = st.selectbox(
            "Jump directly to round",
            options=[
                1,
                2,
                3,
                4,
                5,
                6
            ],
            index=current_round - 1,
            format_func=lambda x:
                f"Round {x}"
        )


        if st.button(
            "🎯 Go to Round",
            width="stretch"
        ):

            (
                supabase
                .table("game_state")
                .update({
                    "current_round":
                        selected_round,

                    "round_status":
                        "open"
                })
                .eq("id", 1)
                .execute()
            )

            st.rerun()


    # -------------------------------------
    # NEXT ROUND
    # -------------------------------------

    with nav3:

        if st.button(
            "Next Round ➡️",
            width="stretch",
            disabled=current_round >= 6
        ):

            (
                supabase
                .table("game_state")
                .update({
                    "current_round":
                        current_round + 1,

                    "round_status":
                        "open"
                })
                .eq("id", 1)
                .execute()
            )

            st.rerun()


    st.divider()


    # =====================================
    # CURRENT QUESTION — INSTRUCTOR VIEW
    # =====================================

    st.subheader("📝 Current Question")


    if current_round == 1:

        st.markdown("""
### Round 1 — The Customer Offer

A customer gives you two payment options:

**A — Take the Cash Now**  
Receive **€180,000 today**

**B — Wait**  
Receive **€220,000 in 2 years**

Your opportunity cost of capital is **8%**.

**Which option creates more value today?**
""")

        with st.expander("🔑 Instructor Answer"):

            pv_a = 180000
            pv_b = 220000 / (1.08 ** 2)

            st.success("✅ Correct answer: B")

            st.write(
                f"Option A: **€{pv_a:,.2f}**  \n"
                f"Option B PV: **€{pv_b:,.2f}**  \n"
                f"Value advantage of B: **€{pv_b - pv_a:,.2f}**"
            )


    elif current_round == 2:

        st.markdown("""
### Round 2 — Equipment Financing

You need new equipment. The supplier offers three payment plans:

**A**  
Pay **€250,000 today**

**B**  
Pay **€95,000 at the end of each year for 3 years**

**C**  
Pay **€75,000 today + €65,000 at the end of each year for 3 years**

Your required return is **9%**.

**Which option has the lowest present value of cost?**
""")

        with st.expander("🔑 Instructor Answer"):

            rate = 0.09

            annuity_factor = (
                1 - (1 + rate) ** -3
            ) / rate

            pv_a = 250000
            pv_b = 95000 * annuity_factor
            pv_c = 75000 + 65000 * annuity_factor

            st.success("✅ Correct answer: C")

            st.write(
                f"A: **€{pv_a:,.2f}**  \n"
                f"B: **€{pv_b:,.2f}**  \n"
                f"C: **€{pv_c:,.2f}**"
            )


    elif current_round == 3:

        st.markdown("""
### Round 3 — The Bank Battle

Your company needs a **€200,000 one-year working-capital loan**.

**A — BlueBank**  
**7.8% APR**, compounded monthly

**B — GreenBank**  
**8.0% effective annual rate**

**C — FlashFinance**  
**7.7% APR**, compounded quarterly

There are no additional fees.

**Which bank offers the lowest effective annual financing cost?**
""")

        with st.expander("🔑 Instructor Answer"):

            ear_a = (
                (1 + 0.078 / 12) ** 12
                - 1
            )

            ear_b = 0.08

            ear_c = (
                (1 + 0.077 / 4) ** 4
                - 1
            )

            st.success(
                "✅ Correct answer: C — FlashFinance"
            )

            st.write(
                f"BlueBank EAR: **{ear_a * 100:.3f}%**  \n"
                f"GreenBank EAR: **{ear_b * 100:.3f}%**  \n"
                f"FlashFinance EAR: **{ear_c * 100:.3f}%**"
            )


    elif current_round == 4:

        st.markdown("""
### Round 4 — The Growth Contract

You are comparing two customer contracts.

**A — Stable Contract**  
Receive **€100,000 at the end of each year for 4 years**

**B — Growth Contract**  
Receive **€94,000 in Year 1**, with the payment growing by **6% per year** for 4 years

Your required return is **10%**.

**Which contract creates more value today?**
""")

        with st.expander("🔑 Instructor Answer"):

            rate = 0.10
            growth = 0.06
            years = 4

            pv_a = (
                100000
                * (
                    1 - (1 + rate) ** -years
                )
                / rate
            )

            pv_b = (
                94000
                / (rate - growth)
                * (
                    1
                    - (
                        (1 + growth)
                        / (1 + rate)
                    ) ** years
                )
            )

            st.success(
                "✅ Correct answer: B — Growth Contract"
            )

            st.write(
                f"Stable Contract: **€{pv_a:,.2f}**  \n"
                f"Growth Contract: **€{pv_b:,.2f}**  \n"
                f"Advantage of B: **€{pv_b - pv_a:,.2f}**"
            )


    elif current_round == 5:

        st.markdown("""
### Round 5 — The Rate Shock 📈

At an **8% required return**, all three projects were worth approximately €150,000.

The required return suddenly increases to **13%**.

| Year | A — Fast Cash | B — Balanced | C — Long Bet |
|---|---:|---:|---:|
| 1 | €100,000 | €0 | €0 |
| 2 | €67,000 | €70,000 | €0 |
| 3 | €0 | €113,400 | €0 |
| 4 | €0 | €0 | €60,000 |
| 5 | €0 | €0 | €155,600 |

**Which project preserves the most value after the rate shock?**
""")

        with st.expander("🔑 Instructor Answer"):

            project_a = [
                100000,
                67000,
                0,
                0,
                0
            ]

            project_b = [
                0,
                70000,
                113400,
                0,
                0
            ]

            project_c = [
                0,
                0,
                0,
                60000,
                155600
            ]

            new_a = pv_cash_flows(
                project_a,
                0.13
            )

            new_b = pv_cash_flows(
                project_b,
                0.13
            )

            new_c = pv_cash_flows(
                project_c,
                0.13
            )

            st.success(
                "✅ Correct answer: A — Fast Cash"
            )

            st.write(
                f"A: **€{new_a:,.2f}**  \n"
                f"B: **€{new_b:,.2f}**  \n"
                f"C: **€{new_c:,.2f}**"
            )


    elif current_round == 6:

        st.markdown("""
### Round 6 — The Founder Decision 🏁

You are the founders of FlowLab.

Your required return is **10%**.

**A — Sell Now**  
Receive **€2.50 million today**

**B — Keep Building**

| Year | Cash Flow |
|---|---:|
| 1 | €500,000 |
| 2 | €600,000 |
| 3 | €700,000 |
| 4 | €800,000 |
| 5 | €1,600,000 |

**C — Wait & Sell**  
Receive **€3.00 million in 2 years**, with no distributions before then.

**Which strategy maximizes shareholder value today?**
""")

        with st.expander("🔑 Instructor Answer"):

            pv_a = 2500000

            pv_b = pv_cash_flows(
                [
                    500000,
                    600000,
                    700000,
                    800000,
                    1600000
                ],
                0.10
            )

            pv_c = (
                3000000
                / (1.10 ** 2)
            )

            st.success(
                "✅ Correct answer: B — Keep Building"
            )

            st.write(
                f"Sell Now: **€{pv_a:,.2f}**  \n"
                f"Keep Building: **€{pv_b:,.2f}**  \n"
                f"Wait & Sell: **€{pv_c:,.2f}**"
            )


    st.divider()


    # =====================================
    # TEAM GRID
    # =====================================

    st.subheader(
        "👥 Team Status"
    )


    for start in range(
        0,
        len(teams),
        5
    ):

        cols = st.columns(5)


        for index, team in enumerate(
            teams[
                start:start + 5
            ]
        ):

            with cols[index]:

                team_id = team["id"]


                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"### {team['teamname']}"
                    )


                    if (
                        team_id
                        not in
                        submissions_by_team
                    ):

                        st.write(
                            "⏳ Waiting"
                        )


                    else:

                        submission = (
                            submissions_by_team[
                                team_id
                            ]
                        )


                        if (
                            round_status
                            != "revealed"
                        ):

                            st.write(
                                "✅ Submitted"
                            )


                        else:

                            decision = (
                                submission[
                                    "decision"
                                ]
                            )

                            correct_decision = (
                                correct_answers.get(
                                    current_round
                                )
                            )


                            if (
                                decision
                                == correct_decision
                            ):

                                st.write(
                                    f"✅ Option {decision}"
                                )

                            else:

                                st.write(
                                    f"❌ Option {decision}"
                                )


    # =====================================
    # REVEAL SECTION
    # =====================================

    if round_status == "revealed":

        st.divider()

        st.subheader(
            "📊 Class Decision"
        )


        # =================================
        # ROUND 1
        # =================================

        if current_round == 1:

            votes_a = count_votes(
                submissions,
                "A"
            )

            votes_b = count_votes(
                submissions,
                "B"
            )


            vote1, vote2 = st.columns(2)


            with vote1:

                st.metric(
                    "Option A",
                    f"{votes_a} teams"
                )


            with vote2:

                st.metric(
                    "Option B",
                    f"{votes_b} teams"
                )


            st.divider()

            st.subheader(
                "💡 Solution"
            )


            pv_a = 180000

            pv_b = (
                220000
                / (1.08 ** 2)
            )


            col_a, col_b = st.columns(2)


            with col_a:

                st.markdown(
                    "### Option A"
                )

                st.metric(
                    "Present Value",
                    f"€{pv_a:,.2f}"
                )


            with col_b:

                st.markdown(
                    "### Option B"
                )

                st.metric(
                    "Present Value",
                    f"€{pv_b:,.2f}"
                )


            st.latex(
                r"PV_B = "
                r"\frac{220,000}{(1.08)^2}"
            )


            st.success(
                "✅ Option B creates more value."
            )


            st.write(
                f"Option B creates approximately "
                f"**€{pv_b - pv_a:,.2f} more "
                f"value today**."
            )


        # =================================
        # ROUND 2
        # =================================

        elif current_round == 2:

            votes_a = count_votes(
                submissions,
                "A"
            )

            votes_b = count_votes(
                submissions,
                "B"
            )

            votes_c = count_votes(
                submissions,
                "C"
            )


            vote1, vote2, vote3 = st.columns(3)


            with vote1:

                st.metric(
                    "Option A",
                    f"{votes_a} teams"
                )


            with vote2:

                st.metric(
                    "Option B",
                    f"{votes_b} teams"
                )


            with vote3:

                st.metric(
                    "Option C",
                    f"{votes_c} teams"
                )


            st.divider()

            st.subheader(
                "💡 Solution"
            )


            rate = 0.09

            annuity_factor = (
                1
                - (1 + rate) ** -3
            ) / rate


            pv_a = 250000

            pv_b = (
                95000
                * annuity_factor
            )

            pv_c = (
                75000
                + 65000
                * annuity_factor
            )


            col_a, col_b, col_c = st.columns(3)


            with col_a:

                st.markdown(
                    "### Option A"
                )

                st.metric(
                    "Present Value",
                    f"€{pv_a:,.2f}"
                )


            with col_b:

                st.markdown(
                    "### Option B"
                )

                st.metric(
                    "Present Value",
                    f"€{pv_b:,.2f}"
                )


            with col_c:

                st.markdown(
                    "### Option C"
                )

                st.metric(
                    "Present Value",
                    f"€{pv_c:,.2f}"
                )


            st.latex(
                r"PV_B = 95,000"
                r"\left["
                r"\frac{1-(1.09)^{-3}}{0.09}"
                r"\right]"
            )


            st.latex(
                r"PV_C = 75,000 + "
                r"65,000"
                r"\left["
                r"\frac{1-(1.09)^{-3}}{0.09}"
                r"\right]"
            )


            st.success(
                "✅ Option C has the lowest "
                "present value of cost."
            )


        # =================================
        # ROUND 3
        # =================================

        elif current_round == 3:

            votes_a = count_votes(
                submissions,
                "A"
            )

            votes_b = count_votes(
                submissions,
                "B"
            )

            votes_c = count_votes(
                submissions,
                "C"
            )


            vote1, vote2, vote3 = st.columns(3)


            with vote1:

                st.metric(
                    "🔵 BlueBank",
                    f"{votes_a} teams"
                )


            with vote2:

                st.metric(
                    "🟢 GreenBank",
                    f"{votes_b} teams"
                )


            with vote3:

                st.metric(
                    "🟠 FlashFinance",
                    f"{votes_c} teams"
                )


            st.divider()

            st.subheader(
                "💡 Solution"
            )


            ear_a = (
                (1 + 0.078 / 12) ** 12
                - 1
            )

            ear_b = 0.08

            ear_c = (
                (1 + 0.077 / 4) ** 4
                - 1
            )


            col_a, col_b, col_c = st.columns(3)


            with col_a:

                st.markdown(
                    "### 🔵 BlueBank"
                )

                st.metric(
                    "EAR",
                    f"{ear_a * 100:.3f}%"
                )


            with col_b:

                st.markdown(
                    "### 🟢 GreenBank"
                )

                st.metric(
                    "EAR",
                    f"{ear_b * 100:.3f}%"
                )


            with col_c:

                st.markdown(
                    "### 🟠 FlashFinance"
                )

                st.metric(
                    "EAR",
                    f"{ear_c * 100:.3f}%"
                )


            st.success(
                "🏆 FlashFinance offers the "
                "cheapest financing."
            )


        # =================================
        # ROUND 4
        # =================================

        elif current_round == 4:

            votes_a = count_votes(
                submissions,
                "A"
            )

            votes_b = count_votes(
                submissions,
                "B"
            )


            vote1, vote2 = st.columns(2)


            with vote1:

                st.metric(
                    "Stable Contract",
                    f"{votes_a} teams"
                )


            with vote2:

                st.metric(
                    "Growth Contract",
                    f"{votes_b} teams"
                )


            st.divider()

            st.subheader(
                "💡 Solution"
            )


            rate = 0.10
            growth = 0.06
            years = 4


            pv_a = (
                100000
                * (
                    1
                    - (1 + rate) ** -years
                )
                / rate
            )


            pv_b = (
                94000
                / (rate - growth)
                * (
                    1
                    - (
                        (1 + growth)
                        / (1 + rate)
                    ) ** years
                )
            )


            col_a, col_b = st.columns(2)


            with col_a:

                st.markdown(
                    "### 📄 Stable Contract"
                )

                st.metric(
                    "Present Value",
                    f"€{pv_a:,.2f}"
                )


            with col_b:

                st.markdown(
                    "### 🚀 Growth Contract"
                )

                st.metric(
                    "Present Value",
                    f"€{pv_b:,.2f}"
                )


            st.success(
                "🚀 Option B — the Growth Contract — "
                "creates more value."
            )


            st.write(
                f"The Growth Contract is worth approximately "
                f"**€{pv_b - pv_a:,.2f} more today**."
            )


        # =================================
        # ROUND 5
        # =================================

        elif current_round == 5:

            votes_a = count_votes(
                submissions,
                "A"
            )

            votes_b = count_votes(
                submissions,
                "B"
            )

            votes_c = count_votes(
                submissions,
                "C"
            )


            vote1, vote2, vote3 = st.columns(3)


            with vote1:

                st.metric(
                    "⚡ Fast Cash",
                    f"{votes_a} teams"
                )


            with vote2:

                st.metric(
                    "⚖️ Balanced",
                    f"{votes_b} teams"
                )


            with vote3:

                st.metric(
                    "🚀 Long Bet",
                    f"{votes_c} teams"
                )


            st.divider()

            st.subheader(
                "💡 What happened after the rate shock?"
            )


            project_a = [
                100000,
                67000,
                0,
                0,
                0
            ]

            project_b = [
                0,
                70000,
                113400,
                0,
                0
            ]

            project_c = [
                0,
                0,
                0,
                60000,
                155600
            ]


            old_rate = 0.08
            new_rate = 0.13


            old_a = pv_cash_flows(
                project_a,
                old_rate
            )

            old_b = pv_cash_flows(
                project_b,
                old_rate
            )

            old_c = pv_cash_flows(
                project_c,
                old_rate
            )


            new_a = pv_cash_flows(
                project_a,
                new_rate
            )

            new_b = pv_cash_flows(
                project_b,
                new_rate
            )

            new_c = pv_cash_flows(
                project_c,
                new_rate
            )


            loss_a = (
                (old_a - new_a)
                / old_a
            ) * 100

            loss_b = (
                (old_b - new_b)
                / old_b
            ) * 100

            loss_c = (
                (old_c - new_c)
                / old_c
            ) * 100


            result_a, result_b, result_c = st.columns(3)


            with result_a:

                st.markdown(
                    "### ⚡ A — Fast Cash"
                )

                st.metric(
                    "PV at 13%",
                    f"€{new_a:,.2f}"
                )

                st.metric(
                    "Value Lost",
                    f"{loss_a:.2f}%"
                )


            with result_b:

                st.markdown(
                    "### ⚖️ B — Balanced"
                )

                st.metric(
                    "PV at 13%",
                    f"€{new_b:,.2f}"
                )

                st.metric(
                    "Value Lost",
                    f"{loss_b:.2f}%"
                )


            with result_c:

                st.markdown(
                    "### 🚀 C — Long Bet"
                )

                st.metric(
                    "PV at 13%",
                    f"€{new_c:,.2f}"
                )

                st.metric(
                    "Value Lost",
                    f"{loss_c:.2f}%"
                )


            st.success(
                "🏆 Option A — Fast Cash — "
                "is the most resilient."
            )


            st.info(
                "Cash flows that arrive sooner are "
                "less sensitive to increases in the "
                "discount rate."
            )


        # =================================
        # ROUND 6
        # =================================

        elif current_round == 6:

            votes_a = count_votes(
                submissions,
                "A"
            )

            votes_b = count_votes(
                submissions,
                "B"
            )

            votes_c = count_votes(
                submissions,
                "C"
            )


            vote1, vote2, vote3 = st.columns(3)


            with vote1:

                st.metric(
                    "💼 Sell Now",
                    f"{votes_a} teams"
                )


            with vote2:

                st.metric(
                    "🚀 Keep Building",
                    f"{votes_b} teams"
                )


            with vote3:

                st.metric(
                    "⏳ Wait & Sell",
                    f"{votes_c} teams"
                )


            st.divider()

            st.subheader(
                "💡 Final Valuation"
            )


            rate = 0.10


            # Option A
            pv_a = 2500000


            # Option B
            operating_cash_flows = [
                500000,
                600000,
                700000,
                800000,
                1600000
            ]


            pv_b = pv_cash_flows(
                operating_cash_flows,
                rate
            )


            # Option C
            pv_c = (
                3000000
                / ((1 + rate) ** 2)
            )


            col_a, col_b, col_c = st.columns(3)


            with col_a:

                st.markdown(
                    "### 💼 Sell Now"
                )

                st.metric(
                    "Value Today",
                    f"€{pv_a:,.2f}"
                )


            with col_b:

                st.markdown(
                    "### 🚀 Keep Building"
                )

                st.metric(
                    "Value Today",
                    f"€{pv_b:,.2f}"
                )


            with col_c:

                st.markdown(
                    "### ⏳ Wait & Sell"
                )

                st.metric(
                    "Value Today",
                    f"€{pv_c:,.2f}"
                )


            st.latex(
                r"PV_B = "
                r"\frac{500,000}{1.10}"
                r"+\frac{600,000}{1.10^2}"
                r"+\frac{700,000}{1.10^3}"
                r"+\frac{800,000}{1.10^4}"
                r"+\frac{1,600,000}{1.10^5}"
            )


            st.latex(
                r"PV_C = "
                r"\frac{3,000,000}{1.10^2}"
            )


            st.success(
                "🏆 Option B — Keep Building — "
                "maximizes shareholder value today."
            )


            st.write(
                f"Keeping the company is worth approximately "
                f"**€{pv_b - pv_a:,.2f} more than "
                f"selling today**."
            )


            st.divider()

            st.title(
                "🏁 CFO Challenge Complete!"
            )


    # =====================================
    # GAME ADMINISTRATION
    # =====================================

    st.divider()

    st.subheader(
        "🧹 Game Administration"
    )


    with st.expander(
        "⚠️ Reset the entire game"
    ):

        st.warning(
            "This will permanently delete ALL team "
            "submissions from Rounds 1–6 and return "
            "the game to Round 1 — OPEN."
        )


        if "confirm_reset" not in st.session_state:

            st.session_state.confirm_reset = False


        # ---------------------------------
        # FIRST CLICK
        # ---------------------------------

        if not st.session_state.confirm_reset:

            if st.button(
                "🧹 Reset Game"
            ):

                st.session_state.confirm_reset = True

                st.rerun()


        # ---------------------------------
        # CONFIRMATION
        # ---------------------------------

        else:

            st.error(
                "Are you sure? This cannot be undone. "
                "All existing submissions will be deleted."
            )


            confirm1, confirm2 = st.columns(2)


            with confirm1:

                if st.button(
                    "✅ Yes, Reset Everything",
                    type="primary",
                    width="stretch"
                ):

                    # DELETE ALL SUBMISSIONS

                    (
                        supabase
                        .table("submissions")
                        .delete()
                        .neq("id", 0)
                        .execute()
                    )


                    # RESET GAME STATE

                    (
                        supabase
                        .table("game_state")
                        .update({
                            "current_round": 1,
                            "round_status": "open"
                        })
                        .eq("id", 1)
                        .execute()
                    )


                    st.session_state.confirm_reset = False


                    st.success(
                        "Game reset successfully."
                    )


                    st.rerun()


            with confirm2:

                if st.button(
                    "❌ Cancel",
                    width="stretch"
                ):

                    st.session_state.confirm_reset = False

                    st.rerun()


# =========================================
# NAVIGATION
# =========================================

instructor = st.Page(
    instructor_page,
    title="Instructor Dashboard",
    icon="📊",
    default=True
)


student = st.Page(
    "pages/1_Student.py",
    title="Student",
    icon="🎮"
)


leaderboard = st.Page(
    "pages/2_Leaderboard.py",
    title="Leaderboard",
    icon="🏆"
)


page = st.navigation(
    [
        instructor,
        student,
        leaderboard
    ]
)


page.run()
