import streamlit as st
import pandas as pd
from supabase import create_client


# =========================================
# SUPABASE CONNECTION
# =========================================

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


# =========================================
# ECONOMIC VALUE CREATED BY EACH DECISION
# =========================================

def round_value_created(round_number, decision):

    # ---------------------------------
    # ROUND 1
    # Customer Offer
    # Higher PV = better
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
    # Lower PV cost = better
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
    # Lower financing cost = better
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
    # Higher PV = better
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

        return values.get(decision, baseline) - baseline


    # ---------------------------------
    # ROUND 5
    # Rate Shock
    # Higher post-shock PV = better
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

        return values.get(decision, baseline) - baseline


    # ---------------------------------
    # ROUND 6
    # Founder Decision
    # Higher company value = better
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

        return values.get(decision, baseline) - baseline


    return 0


# =========================================
# CORRECT ANSWERS
# =========================================

correct_answers = {
    1: "B",
    2: "C",
    3: "C",
    4: "B",
    5: "A",
    6: "B"
}


# =========================================
# READ GAME STATE
# =========================================

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


# =========================================
# DETERMINE WHICH ROUNDS COUNT
# =========================================

if round_status == "revealed":

    completed_rounds = list(
        range(
            1,
            current_round + 1
        )
    )

else:

    completed_rounds = list(
        range(
            1,
            current_round
        )
    )


# =========================================
# READ TEAMS
# =========================================

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


# =========================================
# READ ALL SUBMISSIONS
# =========================================

submissions_response = (
    supabase
    .table("submissions")
    .select("*")
    .execute()
)

all_submissions = submissions_response.data


# =========================================
# BUILD LEADERBOARD
# =========================================

leaderboard = []


for team in teams:

    team_id = team["id"]

    base_equity_value = (
        float(team["ev"])
        + float(team["cash"])
        - float(team["debt"])
    )

    value_created = 0
    correct_decisions = 0
    decisions_made = 0

    # ---------------------------------
    # FIND TEAM SUBMISSIONS
    # ---------------------------------

    team_submissions = [
        submission
        for submission in all_submissions
        if submission["team_id"] == team_id
    ]

    # ---------------------------------
    # SCORE COMPLETED ROUNDS ONLY
    # ---------------------------------

    for submission in team_submissions:

        round_number = submission["round"]

        if round_number not in completed_rounds:
            continue

        decision = submission["decision"]

        decisions_made += 1

        value_created += round_value_created(
            round_number,
            decision
        )

        if (
            decision
            == correct_answers.get(round_number)
        ):

            correct_decisions += 1

    # ---------------------------------
    # FINAL EQUITY VALUE
    # ---------------------------------

    equity_value = (
        base_equity_value
        + value_created
    )

    leaderboard.append({
        "Team": team["teamname"],
        "Base Equity Value": base_equity_value,
        "Value Created": value_created,
        "Equity Value": equity_value,
        "Correct Decisions": correct_decisions,
        "Decisions Made": decisions_made
    })


# =========================================
# SORT LEADERBOARD
# =========================================

leaderboard = sorted(
    leaderboard,
    key=lambda x: (
        x["Equity Value"],
        x["Correct Decisions"]
    ),
    reverse=True
)


# =========================================
# ADD RANK
# =========================================

for rank, team in enumerate(
    leaderboard,
    start=1
):

    team["Rank"] = rank


# =========================================
# PAGE
# =========================================

st.title(
    "🏆 Startup CFO Leaderboard"
)

st.caption(
    "Teams are ranked by the shareholder value created "
    "through their financial decisions."
)


# =========================================
# ROUND STATUS
# =========================================

status1, status2, status3 = st.columns(3)

with status1:

    st.metric(
        "Current Round",
        current_round
    )


with status2:

    st.metric(
        "Rounds Scored",
        len(completed_rounds)
    )


with status3:

    if st.button(
        "🔄 Refresh Leaderboard",
        width="stretch"
    ):

        st.rerun()


st.info(
    "Only revealed rounds count toward the leaderboard. "
    "The current round remains hidden until results are revealed."
)


# =========================================
# PODIUM
# =========================================

if completed_rounds:

    st.divider()

    st.subheader(
        "🥇 Current Podium"
    )

    top_three = leaderboard[:3]

    podium_cols = st.columns(3)

    medals = [
        "🥇",
        "🥈",
        "🥉"
    ]

    for index, team in enumerate(
        top_three
    ):

        with podium_cols[index]:

            with st.container(
                border=True
            ):

                st.markdown(
                    f"## {medals[index]} "
                    f"{team['Team']}"
                )

                st.metric(
                    "Equity Value",
                    f"€{team['Equity Value']:,.0f}"
                )

                st.write(
                    f"Value created: "
                    f"**€{team['Value Created']:,.0f}**"
                )

                st.write(
                    f"Correct decisions: "
                    f"**{team['Correct Decisions']} / "
                    f"{len(completed_rounds)}**"
                )


# =========================================
# FULL TABLE
# =========================================

st.divider()

st.subheader(
    "📊 Full Leaderboard"
)


display_data = []

for team in leaderboard:

    display_data.append({

        "Rank":
            team["Rank"],

        "Team":
            team["Team"],

        "Equity Value":
            f"€{team['Equity Value']:,.0f}",

        "Value Created":
            f"€{team['Value Created']:,.0f}",

        "Correct":
            f"{team['Correct Decisions']} / "
            f"{len(completed_rounds)}"
    })


df = pd.DataFrame(
    display_data
)


st.dataframe(
    df,
    hide_index=True,
    width="stretch"
)


# =========================================
# EXPLANATION
# =========================================

with st.expander(
    "How is company value calculated?"
):

    st.markdown("""
Every team starts with:

- **Enterprise Value:** €1,000,000
- **Cash:** €500,000
- **Debt:** €0

Therefore:

**Starting Equity Value = €1,500,000**

Each financial decision then creates a different amount
of economic value.

For example, in Round 1:

- Option A is worth €180,000 today.
- Option B is worth approximately €188,615 today.

Choosing B therefore creates approximately **€8,615 more
shareholder value** than choosing A.

The same logic is applied throughout the game.

This means the leaderboard rewards the **economic quality of
the decision**, rather than awarding arbitrary points.
""")