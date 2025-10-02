import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import plotly.graph_objects as go
import plotly.express as px
import hashlib

# Page configuration
st.set_page_config(page_title="Smart Parking System", page_icon="🅿️", layout="wide")

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'users_db' not in st.session_state:
    # Simulated user database
    st.session_state.users_db = {}
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'current_booking' not in st.session_state:
    st.session_state.current_booking = None
if 'bookings_history' not in st.session_state:
    st.session_state.bookings_history = []
if 'parking_data' not in st.session_state:
    # Initialize parking facilities
    st.session_state.parking_data = {
        'Select Mall - Saket': {'total': 120, 'available': 45, 'floors': 3},
        'DLF Cyber Hub - Gurgaon': {'total': 200, 'available': 78, 'floors': 4},
        'Phoenix Market City - Mumbai': {'total': 350, 'available': 142, 'floors': 5},
        'Forum Mall - Bangalore': {'total': 180, 'available': 63, 'floors': 3}
    }

def hash_password(password):
    """Hash password for security"""
    return hashlib.sha256(password.encode()).hexdigest()

# Facility data structure
def generate_parking_spots(facility_name, floor_num, total_spots=40):
    """Generate parking spot layout for a floor"""
    spots = []
    rows = 8
    cols = 5
    spot_id = 1
    
    for row in range(rows):
        for col in range(cols):
            status = random.choice(['available', 'occupied', 'available', 'occupied'])
            if random.random() < 0.7:  # 70% chance of being available for demo
                status = 'available'
            
            spots.append({
                'id': f"{floor_num}{chr(65+row)}{spot_id:02d}",
                'row': row,
                'col': col,
                'status': status,
                'type': random.choice(['Regular', 'EV Charging', 'Disabled', 'Regular', 'Regular']),
                'distance_to_entry': abs(row - 0) + abs(col - 2)  # Manhattan distance from entry
            })
            spot_id += 1
    
    return spots

def create_parking_map(spots, assigned_spot=None, route_spots=None):
    """Create interactive parking lot visualization"""
    fig = go.Figure()
    
    # Color mapping
    color_map = {
        'available': '#00D66A',
        'occupied': '#FF4B4B',
        'assigned': '#FFB800'
    }
    
    for spot in spots:
        color = color_map.get(spot['status'], '#00D66A')
        
        if assigned_spot and spot['id'] == assigned_spot:
            color = color_map['assigned']
            marker_size = 20
        else:
            marker_size = 15
        
        # Check if spot is on the route
        is_on_route = route_spots and spot['id'] in route_spots
        
        fig.add_trace(go.Scatter(
            x=[spot['col']],
            y=[spot['row']],
            mode='markers+text',
            marker=dict(
                size=marker_size,
                color=color,
                symbol='square',
                line=dict(width=3, color='#FFB800') if is_on_route else dict(width=1, color='#333')
            ),
            text=spot['id'],
            textposition='middle center',
            textfont=dict(size=8, color='white'),
            hovertemplate=f"<b>Spot: {spot['id']}</b><br>" +
                         f"Status: {spot['status']}<br>" +
                         f"Type: {spot['type']}<br>" +
                         "<extra></extra>",
            showlegend=False
        ))
    
    # Add entry point
    fig.add_trace(go.Scatter(
        x=[2],
        y=[-1],
        mode='markers+text',
        marker=dict(size=25, color='#4A90E2', symbol='triangle-up'),
        text='ENTRY',
        textposition='bottom center',
        textfont=dict(size=12, color='#4A90E2', family='Arial Black'),
        showlegend=False
    ))
    
    fig.update_layout(
        title="Parking Lot Layout",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 6]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-2, 9]),
        plot_bgcolor='#1E1E1E',
        paper_bgcolor='#0E1117',
        height=500,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def calculate_route(start_pos, end_pos):
    """Calculate simple route between two points"""
    route = []
    current = list(start_pos)
    
    # Move horizontally first, then vertically
    while current[1] != end_pos[1]:
        current[1] += 1 if current[1] < end_pos[1] else -1
        route.append(tuple(current))
    
    while current[0] != end_pos[0]:
        current[0] += 1 if current[0] < end_pos[0] else -1
        route.append(tuple(current))
    
    return route

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4A90E2;
        text-align: center;
        margin-bottom: 2rem;
    }
    .welcome-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .booking-card {
        background: #1E1E1E;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #4A90E2;
        margin: 1rem 0;
    }
    .success-msg {
        background: #00D66A;
        color: white;
        padding: 1rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
    }
    .auth-container {
        max-width: 500px;
        margin: 2rem auto;
        padding: 2rem;
        background: #1E1E1E;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .feature-box {
        background: #1E1E1E;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== AUTHENTICATION PAGES ====================

if not st.session_state.authenticated:
    # Welcome Page
    st.markdown('<div class="welcome-header">🅿️ Smart Parking System</div>', unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #888;'>AI-Powered Parking for Modern India</h3>", unsafe_allow_html=True)
    
    # Create tabs for Login and Sign Up
    tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
    
    # LOGIN TAB
    with tab1:
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.subheader("Welcome Back!")
        
        login_email = st.text_input("Email Address", key="login_email", placeholder="your.email@example.com")
        login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            login_btn = st.button("🚀 Login", use_container_width=True, type="primary")
        
        if login_btn:
            if login_email and login_password:
                hashed_pwd = hash_password(login_password)
                
                if login_email in st.session_state.users_db:
                    if st.session_state.users_db[login_email]['password'] == hashed_pwd:
                        st.session_state.authenticated = True
                        st.session_state.user_data = st.session_state.users_db[login_email]
                        st.session_state.user_name = st.session_state.user_data['name']
                        st.session_state.user_phone = st.session_state.user_data['phone']
                        st.session_state.user_vehicle = st.session_state.user_data['vehicle']
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error("❌ Incorrect password!")
                else:
                    st.error("❌ Email not found. Please sign up first!")
            else:
                st.warning("⚠️ Please fill in all fields")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # SIGN UP TAB
    with tab2:
        st.markdown("<div class='auth-container'>", unsafe_allow_html=True)
        st.subheader("Create Your Account")
        
        signup_name = st.text_input("Full Name", key="signup_name", placeholder="Aaryan Kumar")
        signup_email = st.text_input("Email Address", key="signup_email", placeholder="your.email@example.com")
        signup_phone = st.text_input("Phone Number", key="signup_phone", placeholder="9876543210")
        signup_vehicle = st.text_input("Vehicle Number", key="signup_vehicle", placeholder="DL01AB1234")
        signup_password = st.text_input("Create Password", type="password", key="signup_password", placeholder="Minimum 6 characters")
        signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Re-enter password")
        
        signup_btn = st.button("✨ Create Account", use_container_width=True, type="primary")
        
        if signup_btn:
            if signup_name and signup_email and signup_phone and signup_vehicle and signup_password and signup_confirm:
                if len(signup_password) < 6:
                    st.error("❌ Password must be at least 6 characters long!")
                elif signup_password != signup_confirm:
                    st.error("❌ Passwords do not match!")
                elif signup_email in st.session_state.users_db:
                    st.error("❌ Email already registered. Please login!")
                elif not signup_email.count('@') == 1 or not '.' in signup_email.split('@')[1]:
                    st.error("❌ Please enter a valid email address!")
                else:
                    # Create new user
                    st.session_state.users_db[signup_email] = {
                        'name': signup_name,
                        'email': signup_email,
                        'phone': signup_phone,
                        'vehicle': signup_vehicle,
                        'password': hash_password(signup_password),
                        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    st.success("🎉 Account created successfully!")
                    st.balloons()
                    st.info("Please switch to the Login tab to access your account.")
            else:
                st.warning("⚠️ Please fill in all fields")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Features Section
    st.markdown("---")
    st.markdown("<h2 style='text-align: center;'>Why Choose Smart Parking?</h2>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='feature-box'>
            <h3>⚡ Instant Parking</h3>
            <p>Scan QR code and get assigned a spot in seconds. No more searching!</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='feature-box'>
            <h3>🗺️ Smart Navigation</h3>
            <p>Interactive indoor maps guide you directly to your parking spot.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='feature-box'>
            <h3>📅 Pre-Booking</h3>
            <p>Reserve your preferred spot in advance. Plan ahead, park with ease.</p>
        </div>
        """, unsafe_allow_html=True)

# ==================== MAIN APPLICATION (After Authentication) ====================

else:
    # Header
    st.markdown('<div class="main-header">🅿️ Smart Parking Management System</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/parking.png", width=80)
        st.title("Navigation")
        
        st.success(f"Welcome, {st.session_state.user_name}!")
        st.info(f"📧 {st.session_state.user_data['email']}")
        
        page = st.radio("", ["Dashboard", "Quick Park (QR Scan)", "Pre-Book Parking", "My Bookings", "Profile", "Logout"])
    
    # Dashboard
    if page == "Dashboard":
        st.header("📊 Dashboard")
        
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown('<div class="stat-card"><h3>🏢</h3><h2>4</h2><p>Total Facilities</p></div>', unsafe_allow_html=True)
        
        with col2:
            total_spots = sum([v['total'] for v in st.session_state.parking_data.values()])
            st.markdown(f'<div class="stat-card"><h3>🅿️</h3><h2>{total_spots}</h2><p>Total Spots</p></div>', unsafe_allow_html=True)
        
        with col3:
            available_spots = sum([v['available'] for v in st.session_state.parking_data.values()])
            st.markdown(f'<div class="stat-card"><h3>✅</h3><h2>{available_spots}</h2><p>Available Now</p></div>', unsafe_allow_html=True)
        
        with col4:
            total_bookings = len(st.session_state.bookings_history)
            st.markdown(f'<div class="stat-card"><h3>📝</h3><h2>{total_bookings}</h2><p>Your Bookings</p></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Facility availability chart
        st.subheader("🏢 Facility Availability")
        
        facilities_chart_data = pd.DataFrame([
            {"Facility": k, "Available": v['available'], "Occupied": v['total'] - v['available']}
            for k, v in st.session_state.parking_data.items()
        ])
        
        fig = px.bar(facilities_chart_data, x="Facility", y=["Available", "Occupied"],
                     title="Real-time Parking Availability",
                     color_discrete_map={"Available": "#00D66A", "Occupied": "#FF4B4B"},
                     barmode='stack')
        fig.update_layout(plot_bgcolor='#0E1117', paper_bgcolor='#0E1117')
        st.plotly_chart(fig, use_container_width=True)
        
        # Current booking status
        if st.session_state.current_booking:
            st.subheader("🚗 Current Parking Session")
            booking = st.session_state.current_booking
            st.markdown(f"""
            <div class="booking-card">
                <h3>Spot: {booking['spot']}</h3>
                <p><strong>Facility:</strong> {booking['facility']}</p>
                <p><strong>Floor:</strong> {booking['floor']}</p>
                <p><strong>Entry Time:</strong> {booking['entry_time']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🚪 Exit Parking", type="primary"):
                st.session_state.bookings_history.append({
                    **booking,
                    'exit_time': datetime.now().strftime("%I:%M %p")
                })
                st.session_state.current_booking = None
                st.success("✅ Exited successfully!")
                st.rerun()
    
    # Quick Park (QR Scan)
    elif page == "Quick Park (QR Scan)":
        st.header("📱 Quick Park - QR Scan Entry")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Step 1: Scan QR Code")
            st.info("In a real implementation, this would use your camera to scan a QR code at the facility entrance.")
            
            facility = st.selectbox("Select Facility (Simulated QR Scan)", 
                                   list(st.session_state.parking_data.keys()))
            
            if facility:
                data = st.session_state.parking_data[facility]
                st.metric("Available Spots", f"{data['available']}/{data['total']}")
                
                floor = st.selectbox("Select Floor", [f"Floor {i+1}" for i in range(data['floors'])])
                
                spot_preference = st.radio("Spot Preference", 
                                          ["Closest to Entry", "Near Elevator", "Near Exit", "Any Available"])
                
                if st.button("🎯 Assign Parking Spot", type="primary", use_container_width=True):
                    if data['available'] > 0:
                        # Generate spots for selected floor
                        floor_num = int(floor.split()[1])
                        spots = generate_parking_spots(facility, floor_num)
                        
                        # Find best available spot based on preference
                        available_spots = [s for s in spots if s['status'] == 'available']
                        
                        if available_spots:
                            if spot_preference == "Closest to Entry":
                                assigned = min(available_spots, key=lambda x: x['distance_to_entry'])
                            else:
                                assigned = random.choice(available_spots)
                            
                            # Calculate route
                            entry_pos = (0, 2)  # Entry point
                            spot_pos = (assigned['row'], assigned['col'])
                            route = calculate_route(entry_pos, spot_pos)
                            route_spot_ids = [s['id'] for s in spots if (s['row'], s['col']) in route]
                            
                            # Store booking
                            st.session_state.current_booking = {
                                'facility': facility,
                                'floor': floor,
                                'spot': assigned['id'],
                                'entry_time': datetime.now().strftime("%I:%M %p"),
                                'route': route_spot_ids
                            }
                            
                            # Update availability
                            st.session_state.parking_data[facility]['available'] -= 1
                            
                            st.success(f"✅ Spot {assigned['id']} assigned successfully!")
                            st.rerun()
                    else:
                        st.error("❌ No spots available at this facility")
        
        with col2:
            if st.session_state.current_booking:
                booking = st.session_state.current_booking
                
                if booking['facility'] == facility:
                    st.subheader("Step 2: Navigate to Your Spot")
                    st.markdown(f"""
                    <div class="success-msg">
                        Your Spot: {booking['spot']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show map with route
                    floor_num = int(booking['floor'].split()[1])
                    spots = generate_parking_spots(facility, floor_num)
                    
                    # Mark assigned spot
                    for spot in spots:
                        if spot['id'] == booking['spot']:
                            spot['status'] = 'assigned'
                    
                    fig = create_parking_map(spots, booking['spot'], booking.get('route', []))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.info("🧭 Follow the highlighted path to reach your spot")
                    
                    # Navigation instructions
                    st.markdown("### Turn-by-Turn Directions")
                    st.markdown(f"""
                    1. Enter through main gate
                    2. Proceed to **{booking['floor']}**
                    3. Follow the highlighted route
                    4. Park at spot **{booking['spot']}**
                    """)
    
    # Pre-Book Parking
    elif page == "Pre-Book Parking":
        st.header("📅 Pre-Book Your Parking Spot")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Booking Details")
            
            facility = st.selectbox("Select Facility", list(st.session_state.parking_data.keys()))
            
            booking_date = st.date_input("Date", min_value=datetime.now().date())
            booking_time = st.time_input("Arrival Time")
            duration = st.slider("Duration (hours)", 1, 12, 2)
            
            data = st.session_state.parking_data[facility]
            floor = st.selectbox("Preferred Floor", [f"Floor {i+1}" for i in range(data['floors'])])
            
            st.subheader("Spot Preferences")
            spot_type = st.selectbox("Spot Type", ["Regular", "EV Charging", "Disabled"])
            location_pref = st.selectbox("Location", ["Near Entrance", "Near Elevator", "Near Exit", "Any"])
            
            vehicle_size = st.radio("Vehicle Size", ["Compact", "Sedan", "SUV"])
            
            if st.button("🎫 Confirm Booking", type="primary", use_container_width=True):
                floor_num = int(floor.split()[1])
                spots = generate_parking_spots(facility, floor_num)
                available_spots = [s for s in spots if s['status'] == 'available' and s['type'] == spot_type]
                
                if not available_spots:
                    available_spots = [s for s in spots if s['status'] == 'available']
                
                if available_spots:
                    assigned = random.choice(available_spots)
                    
                    booking = {
                        'facility': facility,
                        'floor': floor,
                        'spot': assigned['id'],
                        'date': booking_date.strftime("%d %b %Y"),
                        'time': booking_time.strftime("%I:%M %p"),
                        'duration': duration,
                        'type': spot_type,
                        'status': 'Confirmed'
                    }
                    
                    st.session_state.bookings_history.append(booking)
                    st.success(f"✅ Booking confirmed for {booking['date']} at {booking['time']}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ No spots available matching your preferences")
        
        with col2:
            st.subheader("Booking Summary")
            st.info(f"""
            **Facility:** {facility}
            
            **Date & Time:** {booking_date.strftime('%d %b %Y')} at {booking_time.strftime('%I:%M %p')}
            
            **Duration:** {duration} hours
            
            **Preferences:**
            - Floor: {floor}
            - Type: {spot_type}
            - Location: {location_pref}
            - Vehicle: {vehicle_size}
            """)
            
            # Show facility map preview
            floor_num = int(floor.split()[1])
            spots = generate_parking_spots(facility, floor_num)
            fig = create_parking_map(spots)
            st.plotly_chart(fig, use_container_width=True)
    
    # My Bookings
    elif page == "My Bookings":
        st.header("📋 My Bookings")
        
        if st.session_state.current_booking:
            st.subheader("🟢 Active Parking Session")
            booking = st.session_state.current_booking
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Facility", booking['facility'])
            with col2:
                st.metric("Spot", booking['spot'])
            with col3:
                st.metric("Entry Time", booking['entry_time'])
            
            st.markdown("---")
        
        if st.session_state.bookings_history:
            st.subheader("📅 Booking History")
            
            for idx, booking in enumerate(reversed(st.session_state.bookings_history)):
                with st.expander(f"Booking #{len(st.session_state.bookings_history) - idx} - {booking.get('date', 'Today')}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Facility:** {booking['facility']}")
                        st.write(f"**Spot:** {booking['spot']}")
                        st.write(f"**Floor:** {booking.get('floor', 'N/A')}")
                    
                    with col2:
                        st.write(f"**Date:** {booking.get('date', 'Today')}")
                        st.write(f"**Time:** {booking.get('time', booking.get('entry_time', 'N/A'))}")
                        st.write(f"**Status:** {booking.get('status', 'Completed')}")
        else:
            st.info("No booking history yet. Start parking or pre-book a spot!")
    
    # Profile
    elif page == "Profile":
        st.header("👤 My Profile")
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("""
            <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 3rem; border-radius: 15px; text-align: center;'>
                <h1 style='color: white; font-size: 4rem; margin: 0;'>👤</h1>
                <h2 style='color: white; margin-top: 1rem;'>{}</h2>
            </div>
            """.format(st.session_state.user_name), unsafe_allow_html=True)
        
        with col2:
            st.subheader("Account Information")
            
            st.markdown(f"""
            <div class='booking-card'>
                <p><strong>📧 Email:</strong> {st.session_state.user_data['email']}</p>
                <p><strong>📱 Phone:</strong> {st.session_state.user_data['phone']}</p>
                <p><strong>🚗 Vehicle:</strong> {st.session_state.user_data['vehicle']}</p>
                <p><strong>📅 Member Since:</strong> {st.session_state.user_data.get('created_at', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.subheader("Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Bookings", len(st.session_state.bookings_history))
            with col2:
                st.metric("Active Sessions", 1 if st.session_state.current_booking else 0)
            with col3:
                st.metric("Favorite Facility", "DLF Cyber Hub")
    
    # Logout
    elif page == "Logout":
        st.warning("Are you sure you want to logout?")
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            if st.button("Yes, Logout", type="primary", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user_data = {}
                st.session_state.user_name = ""
                st.session_state.current_booking = None
                st.success("✅ Logged out successfully!")
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>Smart Parking Management System © 2025 | Powered by AI</p>
        <p>🅿️ Making parking hassle-free across India</p>
    </div>
    """, unsafe_allow_html=True)
