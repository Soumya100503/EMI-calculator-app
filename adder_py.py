import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
import base64

# Function to calculate Fixed EMI (Flat Rate)
def calculate_fixed_emi(p, r, n):
    n = n * 12  # Convert years to months
    r = r / (12 * 100)
    emi = p / n + p * r
    interest_payments = [p * r] * n
    principal_payments = [p / n] * n
    return emi, interest_payments, principal_payments

# Function to calculate Reducing Balance EMI
def calculate_reducing_balance_emi(p, r, n):
    n = n * 12  # Convert years to months
    r = r / (12 * 100)
    emi = p * (r * (1 + r)**n) / ((1 + r)**n - 1)
    interest_payments = []
    principal_payments = []
    remaining_principal = p

    for _ in range(n):
        interest_payment = remaining_principal * r
        principal_payment = emi - interest_payment
        interest_payments.append(interest_payment)
        principal_payments.append(principal_payment)
        remaining_principal -= principal_payment

    return emi, interest_payments, principal_payments

# Streamlit App Layout
def get_base64_image(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Encode your logo image
logo_base64 = get_base64_image("image_logo.png")
st.markdown(
    f"""
    <style>
    .header {{
        display: flex;
        align-items: center;
        gap: 15px;
        padding: 10px;
    }}
    .header img {{
        width: 80px; /* Adjust width to resize */
        height: auto;
    }}
    .header .title {{
        font-size: 2em;
        font-weight: bold;
    }}
    </style>
    <div class="header">
        <img src="data:image/png;base64,{logo_base64}" class="logo">
    </div>
    """,
    unsafe_allow_html=True
)

st.title("EMI Calculator and Type Detector")

# Initial Inputs
principal = st.number_input("Enter the principal amount (loan amount)", min_value=0.0)
roi = st.number_input("Enter the rate of interest (annual %)", min_value=0.0)
tenure = st.number_input("Enter the tenure of the loan (years)", min_value=0)

# Session state initialization
if 'emi' not in st.session_state:
    st.session_state.emi = None
    st.session_state.interest_payments = None
    st.session_state.principal_payments = None
    st.session_state.selected_action = None
    st.session_state.selected_emi_type = None
    st.session_state.total_payment = None
    st.session_state.total_interest_paid = None
    st.session_state.monthly_table = None  # Initialize monthly table
    st.session_state.emi_details = None  # Initialize EMI details
    st.session_state.fig = None  # Initialize figure

# Ask for the action
if principal > 0 and roi > 0 and tenure > 0:
    action = st.radio("Choose an action", ('Calculate EMI', 'Check EMI Type'))
    
    # Clear previous state for EMI calculation if action changes
    if st.session_state.selected_action != action:
        st.session_state.emi = None
        st.session_state.interest_payments = None
        st.session_state.principal_payments = None
        st.session_state.monthly_table = None  # Clear monthly table
        st.session_state.emi_details = None  # Clear previous EMI details
        st.session_state.fig = None  # Clear previous figure
        st.session_state.selected_action = action  # Update action

    # Calculate EMI Option
    if action == 'Calculate EMI':
        emi_type = st.radio("Choose the EMI Type", ('Flat Rate EMI', 'Reducing Balance EMI'))

        if st.button("Calculate EMI"):
            if emi_type == 'Flat Rate EMI':
                emi, interest_payments, principal_payments = calculate_fixed_emi(principal, roi, tenure)
            else:
                emi, interest_payments, principal_payments = calculate_reducing_balance_emi(principal, roi, tenure)

            # Store EMI details in session state
            st.session_state.emi = emi
            st.session_state.interest_payments = interest_payments
            st.session_state.principal_payments = principal_payments
            
            # Display EMI details
            total_interest_paid = sum(interest_payments)
            total_payment = principal + total_interest_paid

            st.session_state.total_payment = total_payment
            st.session_state.total_interest_paid = total_interest_paid

            # Show EMI details
            st.session_state.emi_details = (
                f"**Monthly EMI**: {emi:.2f}  \n"
                f"**Total Payment (Principal + Interest)**: {total_payment:.2f}  \n"
                f"**Total Interest Paid Over Loan Tenure**: {total_interest_paid:.2f}"
            )

            # Plotting EMI Breakdown
            months = np.arange(1, tenure * 12 + 1)

            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(months, principal_payments, label="Principal Payment", color="blue", alpha=0.7)
            ax.bar(months, interest_payments, label="Interest Payment", color="red", alpha=0.7, bottom=principal_payments)
            ax.axhline(y=emi, color='black', label=f"EMI Value :Rs. {emi:.2f}", linewidth=2)
    
            # Setting title, labels, and legend
            ax.set_title(f"{emi_type}: Interest vs Principal Payments Over Time")
            ax.set_xlabel("Month")
            ax.set_ylabel("Amount")
            ax.legend()

            st.session_state.fig = fig  # Store the figure in session state

        # Display EMI details
        if st.session_state.emi_details is not None:
            st.markdown(st.session_state.emi_details)  # Show the stored EMI details

        # Display the graph if it has been created
        if st.session_state.fig is not None:
            st.pyplot(st.session_state.fig)  # Show the stored figure

        # Table for Monthly Breakdown in a Specific Year
        st.subheader("Monthly EMI Breakdown for a Specific Year")
        selected_year = st.selectbox("Select the Year for EMI Breakdown", range(1, int(tenure) + 1))

        start_month = (selected_year - 1) * 12
        end_month = start_month + 12
        
        # Ensure the selected year is within the tenure
        if st.session_state.emi is not None and start_month < len(st.session_state.principal_payments):
            end_month = min(end_month, len(st.session_state.principal_payments))  # Adjust end_month to prevent index out of range
            
            monthly_data = {
                "Month": np.arange(1, end_month - start_month + 1),  # Create Month array based on the range
                "Principal Payment": st.session_state.principal_payments[start_month:end_month],
                "Interest Payment": st.session_state.interest_payments[start_month:end_month],
                "Total EMI Payment": [st.session_state.emi] * (end_month - start_month)  # Adjust length
            }

            monthly_df = pd.DataFrame(monthly_data)
            monthly_df.set_index("Month", inplace=True)
            st.session_state.monthly_table = st.empty()  # Create a placeholder for the table
            st.session_state.monthly_table.write(f"Monthly EMI Breakdown for Year {selected_year}")
            st.dataframe(monthly_df, use_container_width=True)

    # Check EMI Type Option
    elif action == 'Check EMI Type':
        input_emi = st.number_input("Enter the EMI amount to check against", min_value=0.0)

        if st.button("Check EMI Type") and input_emi > 0:
            flat_rate_emi, flat_interest_payments, flat_principal_payments = calculate_fixed_emi(principal, roi, tenure)
            reducing_balance_emi, reducing_interest_payments, reducing_principal_payments = calculate_reducing_balance_emi(principal, roi, tenure)

            # Round the EMIs to the nearest tens place for comparison
            rounded_flat_rate_emi = round(flat_rate_emi, -1)  # Round to nearest ten
            rounded_reducing_balance_emi = round(reducing_balance_emi, -1)  # Round to nearest ten
            rounded_input_emi = round(input_emi, -1)  # Round input EMI to nearest ten

            # Check if the input EMI matches either calculated EMI type
            if rounded_input_emi == rounded_flat_rate_emi:
                st.success("The entered EMI corresponds to a Flat Rate EMI.")
                emi, interest_payments, principal_payments = flat_rate_emi, flat_interest_payments, flat_principal_payments
                st.info("Please select 'Calculate EMI' to get the EMI and the yearly schedule.")
            elif rounded_input_emi == rounded_reducing_balance_emi:
                st.success("The entered EMI corresponds to a Reducing Balance EMI.")
                emi, interest_payments, principal_payments = reducing_balance_emi, reducing_interest_payments, reducing_principal_payments
                st.info("Please select 'Calculate EMI' to get the EMI and the yearly schedule.")
            else:
                st.error("You have entered the wrong EMI amount, please check again.")
