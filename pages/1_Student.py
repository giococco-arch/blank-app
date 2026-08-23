import streamlit as st
from supabase import create_client


# =========================================
# SUPABASE CONNECTION
# =========================================
import os
import streamlit as st
from supabase import create_client


# =========================================
# SUPABASE CONNECTION
# =========================================

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Local Codespaces fallback
if not url or not key:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]

supabase = create_client(url, key)
# =========================================
# HELPER FUNCTIONS
# =========================================

def pv_cash_flows(cash_flows, rate):

    return sum(
        cash_flow / ((1 + rate) ** year)
        for year, cash_flow in enumerate(cash_flows, start=1)
    )


def round_value_created(round_number, decision):

    # ---------------------------------
    # ROUND 1
    # Customer Offer
    # Higher PV = more value
    # ---------------------------------

    if round_number == 1:

        values = {
            "A": 180000,
            "B": 220000 / (1.08 ** 2)
        }

        baseline = min(values.values())

        return values.get(decision, baseline) - baseline


    # ---------------------------------
    # ROUND 2
    # Equipment Financing
    # Lower cost = more value
    # ---------------------------------

    elif round_number == 2:

        rate = 0.09

        annuity_factor = (
            1 - (1 + rate) ** -3
        ) / rate

        costs = {
            "A": 250000,
            "B": 95000 * annuity_factor,
            "C": 75000 + 65000 * annuity_factor
        }

        baseline = max(costs.values())

        selected_cost = costs.get(
            decision,
            baseline
        )

        return baseline - selected_cost


    # ---------------------------------
    # ROUND 3
    # Bank Battle
    # Lower financing cost = more value
    # ---------------------------------

    elif round_number == 3:

        loan_amount = 200000

        ear_a = (
            (1 + 0.078 / 12) ** 12
            - 1
        )

        ear_b = 0.08

        ear_c = (
            (1 + 0.077 / 4) ** 4
            - 1
        )

        costs = {
            "A": loan_amount * ear_a,
            "B": loan_amount * ear_b,
            "C": loan_amount * ear_c
        }

        baseline = max(costs.values())

        selected_cost = costs.get(
            decision,
            baseline
        )

        return baseline - selected_cost


    # ---------------------------------
    # ROUND 4
    # Growth Contract
    # Higher PV = more value
    # ---------------------------------

    elif round_number == 4:

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

        values = {
            "A": pv_a,
            "B": pv_b
        }

        baseline = min(values.values())

        return values.get(
            decision,
            baseline
        ) - baseline


    # ---------------------------------
    # ROUND 5
    # Rate Shock
    # Higher post-shock PV = more value
    # ---------------------------------

    elif round_number == 5:

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

        values = {
            "A": pv_cash_flows(
                project_a,
                0.13
            ),

            "B": pv_cash_flows(
                project_b,
                0.13
            ),

            "C": pv_cash_flows(
                project_c,
                0.13
            )
        }

        baseline = min(values.values())

        return values.get(
            decision,
            baseline
        ) - baseline


    # ---------------------------------
    # ROUND 6
    # Founder Decision
    # Higher value = more value created
    # ---------------------------------

    elif round_number == 6:

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

        values = {
            "A": pv_a,
            "B": pv_b,
            "C": pv_c
        }

        baseline = min(values.values())

        return values.get(
            decision,
            baseline
        ) - baseline


    return 0


# =========================================
# SESSION STATE
# =========================================

if "student_team_id" not in st.session_state:
    st.session_state.student_team_id = None

if "student_team_name" not in st.session_state:
    st.session_state.student_team_name = None


# =========================================
# HEADER
# =========================================

st.title("🎮 Startup CFO Challenge")
st.caption("Team Decision Portal")


# =========================================
# LOGIN
# =========================================

if st.session_state.student_team_id is None:

    st.subheader("Join the game")

    team_number = st.selectbox(
        "Select your team",
        range(1, 31),
        format_func=lambda x: f"Team {x}"
    )

    pin = st.text_input(
        "Team PIN",
        type="password",
        max_chars=4
    )

    if st.button(
        "Join Game",
        width="stretch"
    ):

        team_name = f"Team {team_number}"

        response = (
            supabase
            .table("teams")
            .select("id, teamname, pin")
            .eq("teamname", team_name)
            .execute()
        )

        if not response.data:

            st.error(
                "Team not found."
            )

        else:

            team = response.data[0]

            if str(team["pin"]) == str(pin):

                st.session_state.student_team_id = team["id"]
                st.session_state.student_team_name = team["teamname"]

                st.rerun()

            else:

                st.error(
                    "Incorrect PIN."
                )


# =========================================
# GAME
# =========================================

else:

    team_id = st.session_state.student_team_id
    team_name = st.session_state.student_team_name

    st.success(
        f"Logged in as {team_name}"
    )

    # ---------------------------------
    # READ GAME STATE
    # ---------------------------------

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

        st.stop()

    game_state = state_response.data[0]

    current_round = game_state["current_round"]
    round_status = game_state["round_status"]

    # ---------------------------------
    # STATUS
    # ---------------------------------

    status1, status2 = st.columns([3, 1])

    with status1:

        if round_status == "open":

            st.success(
                f"🟢 Round {current_round} is OPEN"
            )

        elif round_status == "locked":

            st.warning(
                f"🔒 Round {current_round} is LOCKED"
            )

        elif round_status == "revealed":

            st.info(
                f"👁 Round {current_round} results are REVEALED"
            )

    with status2:

        if st.button(
            "🔄 Refresh",
            width="stretch"
        ):

            st.rerun()

    # ---------------------------------
    # EXISTING SUBMISSION
    # ---------------------------------

    existing_response = (
        supabase
        .table("submissions")
        .select("*")
        .eq("team_id", team_id)
        .eq("round", current_round)
        .execute()
    )

    existing_submission = (
        existing_response.data[0]
        if existing_response.data
        else None
    )

    st.divider()

    # =========================================
    # ROUND 1
    # =========================================

    if current_round == 1:

        st.subheader(
            "Round 1 — The Customer Offer"
        )

        st.markdown("""
A customer owes your company money.

### Option A
Receive **€180,000 today**

### Option B
Receive **€220,000 in two years**

Your opportunity cost of capital is **8%**.

### Your objective
Choose the option that creates the **highest value today**.
""")

        if round_status == "open":

            if existing_submission:

                st.success(
                    "✅ Your decision has been submitted."
                )

                st.write(
                    f"Your decision: "
                    f"**Option {existing_submission['decision']}**"
                )

            else:

                with st.form(
                    "round_1_form"
                ):

                    decision = st.radio(
                        "Which option do you choose?",
                        ["A", "B"],
                        horizontal=True
                    )

                    calculated_value = st.number_input(
                        "Present value of Option B (€)",
                        min_value=0.0,
                        step=100.0,
                        format="%.2f"
                    )

                    submitted = st.form_submit_button(
                        "🔒 Submit Decision",
                        width="stretch"
                    )

                    if submitted:

                        (
                            supabase
                            .table("submissions")
                            .insert({
                                "team_id": team_id,
                                "round": current_round,
                                "decision": decision,
                                "calculated_value": calculated_value
                            })
                            .execute()
                        )

                        st.rerun()

        elif round_status == "locked":

            if existing_submission:

                st.success(
                    "✅ Your team submitted."
                )

                st.write(
                    f"Your decision: "
                    f"**Option {existing_submission['decision']}**"
                )

                st.info(
                    "Wait for the instructor to reveal the result."
                )

            else:

                st.error(
                    "Your team did not submit."
                )

        elif round_status == "revealed":

            pv_a = 180000

            pv_b = (
                220000
                / (1.08 ** 2)
            )

            if existing_submission:

                if existing_submission["decision"] == "B":

                    st.success(
                        "🎉 Correct! Your team chose Option B."
                    )

                else:

                    st.error(
                        "Your team chose Option A."
                    )

            st.divider()

            st.subheader(
                "💡 Solution"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Option A",
                    f"€{pv_a:,.2f}"
                )

            with col2:

                st.metric(
                    "Option B",
                    f"€{pv_b:,.2f}"
                )

            st.latex(
                r"PV_B = \frac{220,000}{(1.08)^2}"
            )

            st.success(
                "✅ Option B creates more value."
            )


    # =========================================
    # ROUND 2
    # =========================================

    elif current_round == 2:

        st.subheader(
            "Round 2 — Equipment Financing"
        )

        st.markdown("""
Your company needs new production equipment today.

### Option A
Pay **€250,000 today**

### Option B
Pay **€95,000 at the end of each year for 3 years**

### Option C
Pay **€75,000 today** and then  
**€65,000 at the end of each year for 3 years**

Your required return is **9%**.

### Your objective
Choose the financing option with the **lowest present value of cost**.
""")

        if round_status == "open":

            if existing_submission:

                st.success(
                    "✅ Your decision has been submitted."
                )

                st.write(
                    f"Your decision: "
                    f"**Option {existing_submission['decision']}**"
                )

            else:

                with st.form(
                    "round_2_form"
                ):

                    decision = st.radio(
                        "Which option do you choose?",
                        ["A", "B", "C"],
                        horizontal=True
                    )

                    calculated_value = st.number_input(
                        "Present value of your selected option (€)",
                        min_value=0.0,
                        step=100.0,
                        format="%.2f"
                    )

                    submitted = st.form_submit_button(
                        "🔒 Submit Decision",
                        width="stretch"
                    )

                    if submitted:

                        (
                            supabase
                            .table("submissions")
                            .insert({
                                "team_id": team_id,
                                "round": current_round,
                                "decision": decision,
                                "calculated_value": calculated_value
                            })
                            .execute()
                        )

                        st.rerun()

        elif round_status == "locked":

            if existing_submission:

                st.success(
                    "✅ Your team submitted."
                )

                st.write(
                    f"Your decision: "
                    f"**Option {existing_submission['decision']}**"
                )

            else:

                st.error(
                    "Your team did not submit."
                )

        elif round_status == "revealed":

            rate = 0.09

            annuity_factor = (
                1 - (1 + rate) ** -3
            ) / rate

            pv_a = 250000
            pv_b = 95000 * annuity_factor
            pv_c = 75000 + 65000 * annuity_factor

            if existing_submission:

                if existing_submission["decision"] == "C":

                    st.success(
                        "🎉 Correct! Your team chose Option C."
                    )

                else:

                    st.error(
                        f"Your team chose Option "
                        f"{existing_submission['decision']}."
                    )

            st.divider()

            st.subheader(
                "💡 Solution"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "Option A",
                    f"€{pv_a:,.2f}"
                )

            with col2:

                st.metric(
                    "Option B",
                    f"€{pv_b:,.2f}"
                )

            with col3:

                st.metric(
                    "Option C",
                    f"€{pv_c:,.2f}"
                )

            st.success(
                "✅ Option C has the lowest present value of cost."
            )


    # =========================================
    # ROUND 3
    # =========================================

    elif current_round == 3:

        st.subheader(
            "Round 3 — The Bank Battle"
        )

        st.markdown("""
Your company needs a **€200,000 one-year working-capital loan**.

There are no fees and all other contractual terms are identical.

### 🔵 Option A — BlueBank
**7.8% APR**, compounded monthly

### 🟢 Option B — GreenBank
**8.0% effective annual rate**

### 🟠 Option C — FlashFinance
**7.7% APR**, compounded quarterly

### Your objective
Choose the loan with the **lowest effective annual financing cost**.
""")

        if round_status == "open":

            if existing_submission:

                st.success(
                    "✅ Your decision has been submitted."
                )

                st.write(
                    f"Your decision: "
                    f"**Option {existing_submission['decision']}**"
                )

            else:

                with st.form(
                    "round_3_form"
                ):

                    decision = st.radio(
                        "Which bank do you choose?",
                        ["A", "B", "C"],
                        horizontal=True
                    )

                    calculated_value = st.number_input(
                        "EAR of your selected loan (%)",
                        min_value=0.0,
                        max_value=100.0,
                        step=0.001,
                        format="%.3f"
                    )

                    submitted = st.form_submit_button(
                        "🔒 Submit Decision",
                        width="stretch"
                    )

                    if submitted:

                        (
                            supabase
                            .table("submissions")
                            .insert({
                                "team_id": team_id,
                                "round": current_round,
                                "decision": decision,
                                "calculated_value": calculated_value
                            })
                            .execute()
                        )

                        st.rerun()

        elif round_status == "locked":

            if existing_submission:

                st.success(
                    "✅ Your team submitted."
                )

                st.write(
                    f"Your decision: "
                    f"**Option {existing_submission['decision']}**"
                )

            else:

                st.error(
                    "Your team did not submit."
                )

        elif round_status == "revealed":

            ear_a = (
                (1 + 0.078 / 12) ** 12
                - 1
            )

            ear_b = 0.08

            ear_c = (
                (1 + 0.077 / 4) ** 4
                - 1
            )

            if existing_submission:

                if existing_submission["decision"] == "C":

                    st.success(
                        "🎉 Correct! Your team chose FlashFinance."
                    )

                else:

                    st.error(
                        f"Your team chose Option "
                        f"{existing_submission['decision']}."
                    )

            st.divider()

            st.subheader(
                "💡 Solution"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "BlueBank EAR",
                    f"{ear_a * 100:.3f}%"
                )

            with col2:

                st.metric(
                    "GreenBank EAR",
                    f"{ear_b * 100:.3f}%"
                )

            with col3:

                st.metric(
                    "FlashFinance EAR",
                    f"{ear_c * 100:.3f}%"
                )

            st.success(
                "🏆 FlashFinance has the lowest effective annual rate."
            )


    # =========================================
    # ROUND 4
    # =========================================

    elif current_round == 4:

        st.subheader(
            "Round 4 — The Growth Contract"
        )

        st.markdown("""
Your company is negotiating a four-year enterprise customer contract.

Both contracts have the **same risk and service costs**.

### 📄 Option A — Stable Contract
Receive **€100,000 at the end of every year for 4 years**.

### 🚀 Option B — Growth Contract
Receive **€94,000 at the end of Year 1**.

The payment then **grows by 6% every year** for the remaining three years.

Your required return is **10%**.

### Your objective
Choose the contract with the **highest present value**.
""")

        if round_status == "open":

            if existing_submission:

                st.success(
                    "✅ Your decision has been submitted."
                )

                st.write(
                    f"Your decision: "
                    f"**Option {existing_submission['decision']}**"
                )

            else:

                with st.form(
                    "round_4_form"
                ):

                    decision = st.radio(
                        "Which contract do you choose?",
                        ["A", "B"],
                        horizontal=True
                    )

                    calculated_value = st.number_input(
                        "PV of your selected contract (€)",
                        min_value=0.0,
                        step=100.0,
                        format="%.2f"
                    )

                    submitted = st.form_submit_button(
                        "🔒 Submit Decision",
                        width="stretch"
                    )

                    if submitted:

                        (
                            supabase
                            .table("submissions")
                            .insert({
                                "team_id": team_id,
                                "round": current_round,
                                "decision": decision,
                                "calculated_value": calculated_value
                            })
                            .execute()
                        )

                        st.rerun()

        elif round_status == "locked":

            if existing_submission:

                st.success(
                    "✅ Your team submitted."
                )

                st.write(
                    f"Your decision: "
                    f"**Option {existing_submission['decision']}**"
                )

            else:

                st.error(
                    "Your team did not submit."
                )

        elif round_status == "revealed":

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

            if existing_submission:

                if existing_submission["decision"] == "B":

                    st.success(
                        "🎉 Correct! Your team chose the Growth Contract."
                    )

                else:

                    st.error(
                        "Your team chose the Stable Contract."
                    )

            st.divider()

            st.subheader(
                "💡 Solution"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "Stable Contract",
                    f"€{pv_a:,.2f}"
                )

            with col2:

                st.metric(
                    "Growth Contract",
                    f"€{pv_b:,.2f}"
                )

            st.success(
                "🚀 The Growth Contract has the higher present value."
            )


    # =========================================
    # ROUND 5
    # =========================================

    elif current_round == 5:

        st.subheader(
            "Round 5 — The Rate Shock 📈"
        )

        st.markdown("""
Yesterday, your investment committee was considering three projects.

At an **8% required return**, all three projects were worth approximately
**€150,000**.

Overnight, market conditions change.

## 🚨 New required return: 13%

| Year | ⚡ A — Fast Cash | ⚖️ B — Balanced | 🚀 C — Long Bet |
|---|---:|---:|---:|
| 1 | €100,000 | €0 | €0 |
| 2 | €67,000 | €70,000 | €0 |
| 3 | €0 | €113,400 | €0 |
| 4 | €0 | €0 | €60,000 |
| 5 | €0 | €0 | €155,600 |

### Your objective

Which project is **most resilient to the increase in the discount rate**?

Choose the project that preserves the **highest value after the shock**.
""")

        if round_status == "open":

            if existing_submission:

                st.success(
                    "✅ Your decision has been submitted."
                )

                st.write(
                    f"Your decision: "
                    f"**Option {existing_submission['decision']}**"
                )

            else:

                st.warning(
                    "⚠️ Rates have jumped from 8% to 13%."
                )

                with st.form(
                    "round_5_form"
                ):

                    decision = st.radio(
                        "Which project do you choose?",
                        ["A", "B", "C"],
                        horizontal=True
                    )

                    calculated_value = st.number_input(
                        "New PV of your selected project at 13% (€)",
                        min_value=0.0,
                        step=100.0,
                        format="%.2f"
                    )

                    submitted = st.form_submit_button(
                        "🔒 Submit Decision",
                        width="stretch"
                    )

                    if submitted:

                        (
                            supabase
                            .table("submissions")
                            .insert({
                                "team_id": team_id,
                                "round": current_round,
                                "decision": decision,
                                "calculated_value": calculated_value
                            })
                            .execute()
                        )

                        st.rerun()

        elif round_status == "locked":

            if existing_submission:

                st.success(
                    "✅ Your team submitted."
                )

                st.write(
                    f"Your decision: "
                    f"**Option {existing_submission['decision']}**"
                )

            else:

                st.error(
                    "Your team did not submit."
                )

        elif round_status == "revealed":

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

            if existing_submission:

                if existing_submission["decision"] == "A":

                    st.success(
                        "🎉 Correct! Your team chose Fast Cash."
                    )

                else:

                    st.error(
                        f"Your team chose Option "
                        f"{existing_submission['decision']}."
                    )

            st.divider()

            st.subheader(
                "💡 What did the rate shock do?"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.markdown(
                    "### ⚡ Fast Cash"
                )

                st.metric(
                    "PV at 13%",
                    f"€{new_a:,.2f}"
                )

                st.metric(
                    "Value Lost",
                    f"{loss_a:.2f}%"
                )

            with col2:

                st.markdown(
                    "### ⚖️ Balanced"
                )

                st.metric(
                    "PV at 13%",
                    f"€{new_b:,.2f}"
                )

                st.metric(
                    "Value Lost",
                    f"{loss_b:.2f}%"
                )

            with col3:

                st.markdown(
                    "### 🚀 Long Bet"
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
                "🏆 Fast Cash is the most resilient."
            )


    # =========================================
    # ROUND 6
    # =========================================

    elif current_round == 6:

        st.subheader(
            "Round 6 — The Founder Decision 🏁"
        )

        st.markdown("""
You are the founders of FlowLab.

After several years of building the company, you now face your biggest
financial decision.

Your required return is **10%**.

### 💼 Option A — Sell Now
A competitor offers **€2.50 million today**.

You sell the company immediately.

---

### 🚀 Option B — Keep Building

Reject the offer and continue operating the company.

You expect the following cash flows:

| Year | Cash Flow |
|---|---:|
| 1 | €500,000 |
| 2 | €600,000 |
| 3 | €700,000 |
| 4 | €800,000 |
| 5 | €1,600,000 |

---

### ⏳ Option C — Wait & Sell

Reject today's offer.

A strategic buyer is expected to pay **€3.00 million in two years**.

You receive **no cash distributions before the sale**.

---

### Your objective

Which strategy maximizes **shareholder value today**?
""")

        if round_status == "open":

            if existing_submission:

                st.success(
                    "✅ Your final decision has been submitted."
                )

                st.write(
                    f"Your decision: "
                    f"**Option {existing_submission['decision']}**"
                )

                if existing_submission["calculated_value"] is not None:

                    st.write(
                        f"Your estimated value today: "
                        f"**€{existing_submission['calculated_value']:,.2f}**"
                    )

            else:

                st.warning(
                    "🏁 This is your final decision as CFO."
                )

                with st.form(
                    "round_6_form"
                ):

                    decision = st.radio(
                        "What should the founders do?",
                        ["A", "B", "C"],
                        horizontal=True
                    )

                    calculated_value = st.number_input(
                        "Present value of your selected strategy (€)",
                        min_value=0.0,
                        step=1000.0,
                        format="%.2f"
                    )

                    submitted = st.form_submit_button(
                        "🏁 Submit Final Decision",
                        width="stretch"
                    )

                    if submitted:

                        (
                            supabase
                            .table("submissions")
                            .insert({
                                "team_id": team_id,
                                "round": current_round,
                                "decision": decision,
                                "calculated_value": calculated_value
                            })
                            .execute()
                        )

                        st.rerun()

        elif round_status == "locked":

            if existing_submission:

                st.success(
                    "✅ Your team's final decision is locked."
                )

                st.write(
                    f"Your decision: "
                    f"**Option {existing_submission['decision']}**"
                )

            else:

                st.error(
                    "Your team did not submit."
                )

        elif round_status == "revealed":

            rate = 0.10

            pv_a = 2500000

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

            pv_c = (
                3000000
                / ((1 + rate) ** 2)
            )

            if existing_submission:

                team_decision = existing_submission[
                    "decision"
                ]

                if team_decision == "B":

                    st.success(
                        "🎉 Correct! Your team chose to Keep Building."
                    )

                else:

                    st.error(
                        f"Your team chose Option {team_decision}."
                    )

            st.divider()

            st.subheader(
                "💡 Final Valuation"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.markdown(
                    "### 💼 Sell Now"
                )

                st.metric(
                    "Value Today",
                    f"€{pv_a:,.2f}"
                )

            with col2:

                st.markdown(
                    "### 🚀 Keep Building"
                )

                st.metric(
                    "Value Today",
                    f"€{pv_b:,.2f}"
                )

            with col3:

                st.markdown(
                    "### ⏳ Wait & Sell"
                )

                st.metric(
                    "Value Today",
                    f"€{pv_c:,.2f}"
                )

            st.success(
                "🏆 Keep Building creates the highest "
                "shareholder value today."
            )

            st.divider()

            st.title(
                "🏁 Challenge Complete!"
            )


    # =========================================
    # SHAREHOLDER VALUE IMPACT
    # =========================================

    if (
        round_status == "revealed"
        and existing_submission
    ):

        selected_decision = existing_submission[
            "decision"
        ]

        value_created = round_value_created(
            current_round,
            selected_decision
        )

        st.divider()

        st.subheader(
            "💎 Your Shareholder Value Impact"
        )

        st.metric(
            "Value Created This Round",
            f"€{value_created:,.0f}"
        )

        if value_created > 0:

            st.success(
                f"Your decision added approximately "
                f"**€{value_created:,.0f} of shareholder value** "
                f"relative to the least valuable alternative."
            )

        else:

            st.warning(
                "Your decision created **€0 of incremental value** "
                "relative to the least valuable alternative this round."
            )

        st.caption(
            "This is the same economic-value calculation "
            "used in the leaderboard."
        )


    # =========================================
    # LOGOUT
    # =========================================

    st.divider()

    if st.button(
        "Log out"
    ):

        st.session_state.student_team_id = None
        st.session_state.student_team_name = None

        st.rerun()
