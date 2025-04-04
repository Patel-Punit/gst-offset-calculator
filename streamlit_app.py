import streamlit as st
import pandas as pd
import numpy as np

def calculate_gst_offsets(igst_b, cgst_b, sgst_b, igst_l, cgst_l, sgst_l):
    """
    Calculate GST tax offsets based on the given rules.
    
    Parameters:
    - igst_b: IGST balance
    - cgst_b: CGST balance
    - sgst_b: SGST balance
    - igst_l: IGST liability
    - cgst_l: CGST liability
    - sgst_l: SGST liability
    
    Returns:
    Dictionary containing all offset values and remaining liabilities
    """
    # Initialize all offsets to 0
    igst_offset_against_igst = 0
    igst_offset_against_cgst = 0
    igst_offset_against_sgst = 0
    cgst_offset_against_igst = 0
    cgst_offset_against_cgst = 0
    sgst_offset_against_igst = 0
    sgst_offset_against_sgst = 0
    
    # Initialize working variables for balances and liabilities
    rem_igst_b = igst_b
    rem_cgst_b = cgst_b
    rem_sgst_b = sgst_b
    rem_igst_l = igst_l
    rem_cgst_l = cgst_l
    rem_sgst_l = sgst_l
    
    # Calculate potential surpluses and deficits after self-offset
    cgst_surplus = max(0, cgst_b - cgst_l)
    sgst_surplus = max(0, sgst_b - sgst_l)
    cgst_deficit = max(0, cgst_l - cgst_b)
    sgst_deficit = max(0, sgst_l - sgst_b)
    
    # Check if cross-utilization chain is needed
    need_cross_utilization = (cgst_surplus > 0 and sgst_deficit > 0) or (sgst_surplus > 0 and cgst_deficit > 0)
    
    # STEP 1: If cross-utilization is needed, clear IGST liability first using other surpluses
    if need_cross_utilization:
        # First use CGST surplus against IGST liability if possible
        if cgst_surplus > 0 and rem_igst_l > 0:
            cgst_against_igst = min(cgst_surplus, rem_igst_l)
            cgst_offset_against_igst += cgst_against_igst
            rem_cgst_b -= cgst_against_igst
            rem_igst_l -= cgst_against_igst
        
        # Then use SGST surplus against remaining IGST liability if possible
        if sgst_surplus > 0 and rem_igst_l > 0:
            sgst_against_igst = min(sgst_surplus, rem_igst_l)
            sgst_offset_against_igst += sgst_against_igst
            rem_sgst_b -= sgst_against_igst
            rem_igst_l -= sgst_against_igst
        
        # If there's still IGST liability, use IGST balance
        if rem_igst_l > 0 and rem_igst_b > 0:
            igst_against_igst = min(rem_igst_b, rem_igst_l)
            igst_offset_against_igst += igst_against_igst
            rem_igst_b -= igst_against_igst
            rem_igst_l -= igst_against_igst
        
        # Now use IGST balance to offset deficits in CGST and SGST
        if rem_igst_b > 0:
            # First use IGST for CGST deficit if exists
            if rem_cgst_l > min(rem_cgst_b, cgst_l):  # Check if there's still CGST liability after self-offset
                igst_for_cgst = min(rem_igst_b, rem_cgst_l - min(rem_cgst_b, cgst_l))
                igst_offset_against_cgst += igst_for_cgst
                rem_igst_b -= igst_for_cgst
                rem_cgst_l -= igst_for_cgst
            
            # Then use remaining IGST for SGST deficit if exists
            if rem_sgst_l > min(rem_sgst_b, sgst_l):  # Check if there's still SGST liability after self-offset
                igst_for_sgst = min(rem_igst_b, rem_sgst_l - min(rem_sgst_b, sgst_l))
                igst_offset_against_sgst += igst_for_sgst
                rem_igst_b -= igst_for_sgst
                rem_sgst_l -= igst_for_sgst
    else:
        # STEP 2: If no cross-utilization needed, follow standard offset rules
        # First use IGST balance against IGST liability
        igst_offset_against_igst = min(rem_igst_b, rem_igst_l)
        rem_igst_b -= igst_offset_against_igst
        rem_igst_l -= igst_offset_against_igst
    
    # STEP 3: Standard offsetting for remaining balances
    # Use CGST balance against CGST liability
    cgst_for_cgst = min(rem_cgst_b, rem_cgst_l)
    cgst_offset_against_cgst += cgst_for_cgst
    rem_cgst_b -= cgst_for_cgst
    rem_cgst_l -= cgst_for_cgst
    
    # Use SGST balance against SGST liability
    sgst_for_sgst = min(rem_sgst_b, rem_sgst_l)
    sgst_offset_against_sgst += sgst_for_sgst
    rem_sgst_b -= sgst_for_sgst
    rem_sgst_l -= sgst_for_sgst
    
    # STEP 4: Use any remaining IGST balance optimally
    if rem_igst_b > 0:
        # If we still have CGST liability, use IGST
        if rem_cgst_l > 0:
            additional_igst_for_cgst = min(rem_igst_b, rem_cgst_l)
            igst_offset_against_cgst += additional_igst_for_cgst
            rem_igst_b -= additional_igst_for_cgst
            rem_cgst_l -= additional_igst_for_cgst
        
        # If we still have SGST liability, use remaining IGST
        if rem_igst_l == 0 and rem_sgst_l > 0 and rem_igst_b > 0:
            additional_igst_for_sgst = min(rem_igst_b, rem_sgst_l)
            igst_offset_against_sgst += additional_igst_for_sgst
            rem_igst_b -= additional_igst_for_sgst
            rem_sgst_l -= additional_igst_for_sgst
    
    # STEP 5: Use any remaining CGST/SGST balances for IGST liability if needed
    if rem_igst_l > 0:
        # Use remaining CGST balance for IGST liability
        if rem_cgst_b > 0:
            additional_cgst_for_igst = min(rem_cgst_b, rem_igst_l)
            cgst_offset_against_igst += additional_cgst_for_igst
            rem_cgst_b -= additional_cgst_for_igst
            rem_igst_l -= additional_cgst_for_igst
        
        # Use remaining SGST balance for IGST liability
        if rem_sgst_b > 0 and rem_igst_l > 0:
            additional_sgst_for_igst = min(rem_sgst_b, rem_igst_l)
            sgst_offset_against_igst += additional_sgst_for_igst
            rem_sgst_b -= additional_sgst_for_igst
            rem_igst_l -= additional_sgst_for_igst
    
    # Calculate remaining balances and cash payments required
    remaining_igst_balance = rem_igst_b
    remaining_cgst_balance = rem_cgst_b
    remaining_sgst_balance = rem_sgst_b
    
    cash_payment_igst = max(0, rem_igst_l)
    cash_payment_cgst = max(0, rem_cgst_l)
    cash_payment_sgst = max(0, rem_sgst_l)
    total_cash_payment = cash_payment_igst + cash_payment_cgst + cash_payment_sgst
    
    return {
        "igst_offset_against_igst": igst_offset_against_igst,
        "igst_offset_against_cgst": igst_offset_against_cgst,
        "igst_offset_against_sgst": igst_offset_against_sgst,
        "cgst_offset_against_igst": cgst_offset_against_igst,
        "cgst_offset_against_cgst": cgst_offset_against_cgst,
        "sgst_offset_against_igst": sgst_offset_against_igst,
        "sgst_offset_against_sgst": sgst_offset_against_sgst,
        "remaining_igst_balance": remaining_igst_balance,
        "remaining_cgst_balance": remaining_cgst_balance,
        "remaining_sgst_balance": remaining_sgst_balance,
        "cash_payment_igst": cash_payment_igst,
        "cash_payment_cgst": cash_payment_cgst,
        "cash_payment_sgst": cash_payment_sgst,
        "total_cash_payment": total_cash_payment
    }
    
    # Step 3: Distribute remaining IGST balance optimally between CGST and SGST
    if rem_igst_b > 0 and (rem_cgst_l > 0 or rem_sgst_l > 0):
        # Calculate total remaining CS liability
        total_cs_liability = rem_cgst_l + rem_sgst_l
        
        if rem_igst_b >= total_cs_liability:
            # IGST can cover all remaining liabilities
            igst_offset_against_cgst += rem_cgst_l
            igst_offset_against_sgst += rem_sgst_l
            rem_igst_b -= (rem_cgst_l + rem_sgst_l)
            rem_cgst_l = 0
            rem_sgst_l = 0
        else:
            # Need to distribute proportionally
            if total_cs_liability > 0:
                cgst_proportion = rem_cgst_l / total_cs_liability
                
                # Calculate how much IGST to allocate to CGST
                additional_igst_for_cgst = min(rem_cgst_l, round(rem_igst_b * cgst_proportion, 2))
                igst_offset_against_cgst += additional_igst_for_cgst
                rem_igst_b -= additional_igst_for_cgst
                rem_cgst_l -= additional_igst_for_cgst
                
                # Use any remaining IGST for SGST
                additional_igst_for_sgst = min(rem_sgst_l, rem_igst_b)
                igst_offset_against_sgst += additional_igst_for_sgst
                rem_igst_b -= additional_igst_for_sgst
                rem_sgst_l -= additional_igst_for_sgst
    
    # Step 4: Use any remaining CGST and SGST balances for IGST liability
    if rem_igst_l > 0:
        # Use remaining CGST balance for IGST liability
        if rem_cgst_b > 0:
            additional_cgst_for_igst = min(rem_cgst_b, rem_igst_l)
            cgst_offset_against_igst += additional_cgst_for_igst
            rem_cgst_b -= additional_cgst_for_igst
            rem_igst_l -= additional_cgst_for_igst
        
        # Use remaining SGST balance for IGST liability
        if rem_sgst_b > 0:
            additional_sgst_for_igst = min(rem_sgst_b, rem_igst_l)
            sgst_offset_against_igst += additional_sgst_for_igst
            rem_sgst_b -= additional_sgst_for_igst
            rem_igst_l -= additional_sgst_for_igst
    
    # Calculate remaining balances and cash payments required
    remaining_igst_balance = rem_igst_b
    remaining_cgst_balance = rem_cgst_b
    remaining_sgst_balance = rem_sgst_b
    
    cash_payment_igst = max(0, rem_igst_l)
    cash_payment_cgst = max(0, rem_cgst_l)
    cash_payment_sgst = max(0, rem_sgst_l)
    total_cash_payment = cash_payment_igst + cash_payment_cgst + cash_payment_sgst
    
    return {
        "igst_offset_against_igst": igst_offset_against_igst,
        "igst_offset_against_cgst": igst_offset_against_cgst,
        "igst_offset_against_sgst": igst_offset_against_sgst,
        "cgst_offset_against_igst": cgst_offset_against_igst,
        "cgst_offset_against_cgst": cgst_offset_against_cgst,
        "sgst_offset_against_igst": sgst_offset_against_igst,
        "sgst_offset_against_sgst": sgst_offset_against_sgst,
        "remaining_igst_balance": remaining_igst_balance,
        "remaining_cgst_balance": remaining_cgst_balance,
        "remaining_sgst_balance": remaining_sgst_balance,
        "cash_payment_igst": cash_payment_igst,
        "cash_payment_cgst": cash_payment_cgst,
        "cash_payment_sgst": cash_payment_sgst,
        "total_cash_payment": total_cash_payment
    }

# Streamlit app
st.set_page_config(page_title="GST Tax Offset Calculator", layout="wide")

st.title("GST Tax Offset Calculator")

# Create three columns for input
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Available Balances")
    igst_b = st.number_input("IGST Balance", min_value=0.0, value=0.0, step=100.0)
    cgst_b = st.number_input("CGST Balance", min_value=0.0, value=0.0, step=100.0)
    sgst_b = st.number_input("SGST Balance", min_value=0.0, value=0.0, step=100.0)
    total_balance = igst_b + cgst_b + sgst_b
    st.info(f"Total Balance: {total_balance:.2f}")

with col2:
    st.subheader("Tax Liabilities")
    igst_l = st.number_input("IGST Liability", min_value=0.0, value=0.0, step=100.0)
    cgst_l = st.number_input("CGST Liability", min_value=0.0, value=0.0, step=100.0)
    sgst_l = st.number_input("SGST Liability", min_value=0.0, value=0.0, step=100.0)
    total_liability = igst_l + cgst_l + sgst_l
    st.info(f"Total Liability: {total_liability:.2f}")

with col3:
    st.subheader("Summary")
    st.write("Total Balance: ", f"₹ {total_balance:.2f}")
    st.write("Total Liability: ", f"₹ {total_liability:.2f}")
    difference = total_balance - total_liability
    
    if difference >= 0:
        st.success(f"Surplus: ₹ {difference:.2f}")
    else:
        st.error(f"Deficit: ₹ {abs(difference):.2f}")

# Button to calculate offsets
if st.button("Calculate Offsets"):
    result = calculate_gst_offsets(igst_b, cgst_b, sgst_b, igst_l, cgst_l, sgst_l)
    
    # Display offsets
    st.subheader("Offset Details")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("IGST Offsets:")
        st.info(f"Against IGST: ₹ {result['igst_offset_against_igst']:.2f}")
        st.info(f"Against CGST: ₹ {result['igst_offset_against_cgst']:.2f}")
        st.info(f"Against SGST: ₹ {result['igst_offset_against_sgst']:.2f}")
        total_igst_offset = result['igst_offset_against_igst'] + result['igst_offset_against_cgst'] + result['igst_offset_against_sgst']
        st.success(f"Total IGST Utilized: ₹ {total_igst_offset:.2f}")
    
    with col2:
        st.write("CGST Offsets:")
        st.info(f"Against CGST: ₹ {result['cgst_offset_against_cgst']:.2f}")
        st.info(f"Against IGST: ₹ {result['cgst_offset_against_igst']:.2f}")
        total_cgst_offset = result['cgst_offset_against_cgst'] + result['cgst_offset_against_igst']
        st.success(f"Total CGST Utilized: ₹ {total_cgst_offset:.2f}")
    
    with col3:
        st.write("SGST Offsets:")
        st.info(f"Against SGST: ₹ {result['sgst_offset_against_sgst']:.2f}")
        st.info(f"Against IGST: ₹ {result['sgst_offset_against_igst']:.2f}")
        total_sgst_offset = result['sgst_offset_against_sgst'] + result['sgst_offset_against_igst']
        st.success(f"Total SGST Utilized: ₹ {total_sgst_offset:.2f}")
    
    # Display remaining balances and cash payments
    st.subheader("Remaining Balances")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"Remaining IGST Balance: ₹ {result['remaining_igst_balance']:.2f}")
    
    with col2:
        st.info(f"Remaining CGST Balance: ₹ {result['remaining_cgst_balance']:.2f}")
    
    with col3:
        st.info(f"Remaining SGST Balance: ₹ {result['remaining_sgst_balance']:.2f}")
    
    # Display cash payments
    st.subheader("Cash Payments Required")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.error(f"IGST Cash Payment: ₹ {result['cash_payment_igst']:.2f}")
    
    with col2:
        st.error(f"CGST Cash Payment: ₹ {result['cash_payment_cgst']:.2f}")
    
    with col3:
        st.error(f"SGST Cash Payment: ₹ {result['cash_payment_sgst']:.2f}")
    
    with col4:
        st.error(f"Total Cash Payment: ₹ {result['total_cash_payment']:.2f}")
    
    # Create data for offset matrix visualization
    st.subheader("Offset Matrix")
    offset_data = {
        "Offset From": ["IGST Balance", "CGST Balance", "SGST Balance", "Cash Payment", "Total"],
        "IGST Liability": [
            result['igst_offset_against_igst'],
            result['cgst_offset_against_igst'],
            result['sgst_offset_against_igst'],
            result['cash_payment_igst'],
            igst_l
        ],
        "CGST Liability": [
            result['igst_offset_against_cgst'],
            result['cgst_offset_against_cgst'],
            0,
            result['cash_payment_cgst'],
            cgst_l
        ],
        "SGST Liability": [
            result['igst_offset_against_sgst'],
            0,
            result['sgst_offset_against_sgst'],
            result['cash_payment_sgst'],
            sgst_l
        ],
        "Total": [
            total_igst_offset,
            total_cgst_offset,
            total_sgst_offset,
            result['total_cash_payment'],
            total_liability
        ]
    }
    
    df = pd.DataFrame(offset_data)
    st.table(df.style.format(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else x))

    # Verification
    st.subheader("Verification")
    total_offset = total_igst_offset + total_cgst_offset + total_sgst_offset
    total_remaining_balance = result['remaining_igst_balance'] + result['remaining_cgst_balance'] + result['remaining_sgst_balance']
    
    verification_data = {
        "Item": ["Initial Balance", "Total Utilized", "Remaining Balance", "Initial Liability", "Cash Payment"],
        "IGST": [igst_b, total_igst_offset, result['remaining_igst_balance'], igst_l, result['cash_payment_igst']],
        "CGST": [cgst_b, total_cgst_offset, result['remaining_cgst_balance'], cgst_l, result['cash_payment_cgst']],
        "SGST": [sgst_b, total_sgst_offset, result['remaining_sgst_balance'], sgst_l, result['cash_payment_sgst']],
        "Total": [total_balance, total_offset, total_remaining_balance, total_liability, result['total_cash_payment']]
    }
    
    df_verification = pd.DataFrame(verification_data)
    st.table(df_verification.style.format(lambda x: f"{x:.2f}" if isinstance(x, (int, float)) else x))
    
    # Final check
    if abs(total_balance - total_offset - total_remaining_balance) < 0.01 and abs(total_liability - total_offset - result['total_cash_payment']) < 0.01:
        st.success("✅ Verification Successful: All balances and liabilities are accounted for correctly.")
    else:
        st.error("❌ Verification Failed: There may be a calculation error.")

# Add footer
st.markdown("---")
st.markdown("GST Offset Calculator - Based on Indian GST rules")
