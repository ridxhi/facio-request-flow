
import streamlit as st

st.set_page_config(page_title="Facio Request Flow", page_icon="📋")

# Save requests while someone is using the demo
if "requests" not in st.session_state:
    st.session_state.requests = []

# Let us switch between users to test both sides of the app
user = st.sidebar.selectbox(
    "Demo user",
    ["Broker A", "Broker B", "Reviewer"]
)

broker_id = {
    "Broker A": "broker_001",
    "Broker B": "broker_002"
}.get(user)

st.title("Facio Request Flow")
st.write("Submit an insurance request and see what happens next.")

# Brokers get two tabs, while reviewers only see their review page
if user == "Reviewer":
    reviewer_tab = st.container()
else:
    new_request_tab, my_requests_tab = st.tabs(
        ["New Request", "My Requests"]
    )

# Broker side: fill out and submit a new request
if user != "Reviewer":
    with new_request_tab:
        st.subheader("New Insurance Request")

        business_name = st.text_input("Business name")

        activity = st.selectbox(
            "Business activity",
            ["Select an activity", "Retail", "Consulting", "Other"]
        )

        # Only ask for more details if the business activity is Other
        other_activity = ""
        if activity == "Other":
            other_activity = st.text_input("Please specify the business activity")

        revenue = st.number_input(
            "Annual revenue (USD)",
            min_value=0,
            step=1000,
            value=0
        )

        claims = st.radio(
            "Has the business had insurance claims in the past 3 years?",
            ["No", "Yes"],
            index=None
        )

        # If they had claims, we need a short explanation
        claim_description = ""
        if claims == "Yes":
            claim_description = st.text_area("Briefly describe the claims")

        if st.button("Submit request"):

            # Check that all the required information is filled out
            if business_name.strip() == "":
                st.error("Please enter the business name.")

            elif activity == "Select an activity":
                st.error("Please select the business activity.")

            elif activity == "Other" and other_activity.strip() == "":
                st.error("Please specify the business activity.")

            elif claims is None:
                st.error("Please answer the insurance claims question.")

            elif claims == "Yes" and claim_description.strip() == "":
                st.error("Please describe the insurance claims.")

            else:
                # Requests that meet all three rules can skip manual review
                if (
                    activity in ["Retail", "Consulting"]
                    and revenue <= 500000
                    and claims == "No"
                ):
                    status = "Ready for quotation"
                    next_step = "No action needed. Your request is ready for the quotation stage."
                else:
                    status = "Needs review"
                    next_step = "Waiting for a reviewer. No action needed from you."

                # Keep the request details together so we can use them later
                request = {
                    "id": len(st.session_state.requests) + 1,
                    "broker_id": broker_id,
                    "business_name": business_name.strip(),
                    "activity": other_activity.strip() if activity == "Other" else activity,
                    "revenue": revenue,
                    "claims": claims,
                    "claim_description": claim_description.strip(),
                    "status": status,
                    "next_step": next_step,
                    "reviewer_question": "",
                    "broker_response": ""
                }

                st.session_state.requests.append(request)

                st.success(f"{request['business_name']} submitted successfully!")
                st.info(f"Status: {status}")
                st.write(next_step)


# Broker side: only show requests submitted by this broker
if user != "Reviewer":
    with my_requests_tab:
        st.subheader("My Requests")

        my_requests = [
            request for request in st.session_state.requests
            if request["broker_id"] == broker_id
        ]

        if not my_requests:
            st.info("You haven't submitted any requests yet.")

        for request in my_requests:
            with st.expander(
                f"{request['business_name']} — {request['status']}"
            ):
                st.write(f"**Activity:** {request['activity']}")
                st.write(f"**Annual revenue:** ${request['revenue']:,.0f}")
                st.write(f"**Claims in past 3 years:** {request['claims']}")

                if request["claims"] == "Yes":
                    st.write(f"**Claim details:** {request['claim_description']}")

                st.write(f"**Status:** {request['status']}")
                st.info(request["next_step"])

                # Let the broker answer if the reviewer needs more information
                if request["status"] == "More information needed":
                    st.warning(
                        f"Reviewer question: {request['reviewer_question']}"
                    )

                    response = st.text_area(
                        "Your response",
                        key=f"response_{request['id']}"
                    )

                    if st.button(
                        "Send Response",
                        key=f"respond_{request['id']}"
                    ):
                        if response.strip() == "":
                            st.error("Please enter a response.")
                        else:
                            request["broker_response"] = response.strip()
                            request["status"] = "Needs review"
                            request["next_step"] = (
                                "Your response was sent. "
                                "Waiting for the reviewer."
                            )
                            st.rerun()

                st.caption(
                    "Ready for quotation does not mean insurance "
                    "has been approved or purchased."
                )


# Reviewer side: look at requests that need a decision
if user == "Reviewer":
    with reviewer_tab:
        st.subheader("Requests Needing Review")

        review_requests = [
            request for request in st.session_state.requests
            if request["status"] == "Needs review"
        ]

        if not review_requests:
            st.info("No requests currently need review.")

        for request in review_requests:
            with st.expander(
                f"{request['business_name']} — {request['status']}"
            ):
                st.write(f"**Business activity:** {request['activity']}")
                st.write(f"**Annual revenue:** ${request['revenue']:,.0f}")
                st.write(f"**Claims:** {request['claims']}")

                if request["claims"] == "Yes":
                    st.write(
                        f"**Claim description:** {request['claim_description']}"
                    )

                st.write(f"**Current status:** {request['status']}")

                # Show the broker's answer before the reviewer makes a decision
                if request["broker_response"] != "":
                    st.info("Broker's response:")
                    st.write(request["broker_response"])

                # Reviewer can move the request to the quotation stage
                if st.button(
                    "Mark Ready for Quotation",
                    key=f"ready_{request['id']}"
                ):
                    request["status"] = "Ready for quotation"
                    request["next_step"] = (
                        "Your request is ready for the quotation stage. "
                        "No action is needed from you."
                    )
                    st.rerun()

                question = st.text_area(
                    "Ask the broker for more information",
                    key=f"question_{request['id']}"
                )

                # Send the request back to the broker if something is missing
                if st.button(
                    "Request Information",
                    key=f"ask_{request['id']}"
                ):
                    if question.strip() == "":
                        st.error("Please enter a question for the broker.")
                    else:
                        request["reviewer_question"] = question.strip()
                        request["status"] = "More information needed"
                        request["next_step"] = (
                            "A reviewer needs more information from you. "
                            "Please respond to the question below."
                        )
                        st.rerun()
