import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import plotly.graph_objects as go
import plotly.express as px

# Page configuration
st.set_page_config(page_title="Smart Parking System", page_icon="🅿️", layout="wide")

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
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
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">🅿️ Smart Parking Management System</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/parking.png", width=80)
    st.title("Navigation")
    
    if not st.session_state.logged_in:
        page = st.radio("", ["Login", "About"])
    else:
        st.success(f"Welcome, {st.session_state.user_name}!")
        page = st.radio("", ["Dashboard", "Quick Park (QR Scan)", "Pre-Book Parking", "My Bookings", "Logout"])

# Login Page
if page == "Login" and not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("🔐 User Login")
        name = st.text_input("Full Name")
        phone = st.text_input("Phone Number")
        vehicle = st.text_input("Vehicle Number")
        
        if st.button("Login", use_container_width=True):
            if name and phone and vehicle:
                st.session_state.logged_in = True
                st.session_state.user_name = name
                st.session_state.user_phone = phone
                st.session_state.user_vehicle = vehicle
                st.rerun()
            else:
                st.error("Please fill all fields")

# About Page
elif page == "About":
    st.header("About Smart Parking System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Key Features")
        st.markdown("""
        - **Instant QR Scan Entry**: Quick access to parking facilities
        - **Real-time Spot Assignment**: AI-powered optimal spot allocation
        - **Indoor Navigation**: Turn-by-turn guidance to your spot
        - **Pre-booking**: Reserve spots in advance
        - **Custom Preferences**: Choose spots based on your needs
        - **Traffic Flow Optimization**: Smooth entry and exit
        """)
    
    with col2:
        st.subheader("🚗 How It Works")
        st.markdown("""
        1. **Scan QR Code** at the facility entrance
        2. **Get Assigned** an optimal parking spot
        3. **Follow the Route** on your device
        4. **Park & Go** - hassle-free experience
        
        Or **Pre-book** your spot before arriving!
        """)
    
    st.subheader("🏢 Available Facilities")
    facilities_df = pd.DataFrame([
        {"Facility": k, "Total Spots": v['total'], "Available": v['available'], "Floors": v['floors']}
        for k, v in st.session_state.parking_data.items()
    ])
    st.dataframe(facilities_df, use_container_width=True)

# Dashboard
elif page == "Dashboard":
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

# Logout
elif page == "Logout":
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.session_state.current_booking = None
    st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Smart Parking Management System © 2025 | Powered by AI</p>
    <p>🅿️ Making parking hassle-free across India</p>
</div>
""", unsafe_allow_html=True)