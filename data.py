import streamlit as st
import pandas as pd
import re
from connect import cred
import gspread
from google.auth.exceptions import RefreshError, TransportError


class DeeperLifeSurvey:
    def __init__(self):
        self.initialize_session_state()
        self.zone = None
        self.region = None
        self.division = None

        # Initialize data frame here so it exists before other methods use it
        try:
            self.df = pd.read_csv(r"zone - Original.csv")
            self.df.columns = [col.strip() for col in self.df.columns]  # Clean column names
        except FileNotFoundError:
            st.error(
                "Error: The CSV file was not found. Please make sure "
                "'zone - Original.csv' is in the correct directory."
            )
            self.df = pd.DataFrame(columns=['ZONE', 'REGION', 'DIVISION'])  # Empty fallback

        

    def initialize_session_state(self):
        if "teaching_staff" not in st.session_state:
            st.session_state.teaching_staff = []
        if "non_teaching_staff" not in st.session_state:
            st.session_state.non_teaching_staff = []
        if "committee_members" not in st.session_state:
            st.session_state.committee_members = []
        if "class_data" not in st.session_state:
            st.session_state.class_data = {
                "Creche/Nursery": {"males": 0, "females": 0, "tuition": 0},
                "K.G 1": {"males": 0, "females": 0, "tuition": 0},
                "K.G 2": {"males": 0, "females": 0, "tuition": 0},
                "Class 1": {"males": 0, "females": 0, "tuition": 0},
                "Class 2": {"males": 0, "females": 0, "tuition": 0},
                "Class 3": {"males": 0, "females": 0, "tuition": 0},
                "Class 4": {"males": 0, "females": 0, "tuition": 0},
                "Class 5": {"males": 0, "females": 0, "tuition": 0},
                "Class 6": {"males": 0, "females": 0, "tuition": 0},
                "JHS 1": {"males": 0, "females": 0, "tuition": 0},
                "JHS 2": {"males": 0, "females": 0, "tuition": 0},
                "JHS 3": {"males": 0, "females": 0, "tuition": 0}
            }

    def format_name(self, name):
        """Capitalize names properly"""
        return " ".join(word.capitalize() for word in name.split())
    
    def validate_phone(self, number):
        """Validate 10-digit phone number"""
        return re.match(r'^\d{10}$', number) is not None

    def school_info_section(self):
        with st.container(border=True):
            st.subheader("Basic Information")

            zones = self.df['ZONE'].unique()
            self.zone = st.selectbox("Zone*", options=zones, index=None, placeholder="Select a zone...")

            if self.zone:
                regions = self.df[self.df['ZONE'] == self.zone]['REGION'].unique()
                self.region = st.selectbox("Region*", options=regions, index=None, placeholder="Select a region...")

            if self.region:
                divisions = self.df[self.df['REGION'] == self.region]['DIVISION'].unique()
                self.division = st.selectbox("Division*", options=divisions, index=None, placeholder="Select a division...")

            self.school_name = st.text_input("Name of School*", max_chars=100).strip()
            self.head_teacher = st.text_input("Name of Head Teacher*", max_chars=100).strip()
            
            col1, col2 = st.columns(2)
            self.phone = col1.text_input("Phone Number of Head Teacher*", max_chars=10)
            self.whatsapp = col2.text_input("WhatsApp Number of Head Teacher*", max_chars=10)
            
            if self.phone and not self.validate_phone(self.phone):
                col1.error("Must be 10 digits")
            if self.whatsapp and not self.validate_phone(self.whatsapp):
                col2.error("Must be 10 digits")

    def staff_section(self, staff_type, education_options, max_value=50):
        with st.container(border=True):
            st.subheader(f"{staff_type.replace('_', ' ').title()} Staff")
            num_staff = st.number_input(
                f"Number of {staff_type.replace('_', ' ')} Staff*",
                min_value=0,
                max_value=max_value,
                step=1
            )
            
            staff_data = []
            if num_staff > 0:
                st.write(f"**Enter details for {num_staff} {staff_type.replace('_', ' ')} staff:**")
                for i in range(num_staff):
                    with st.expander(f"Staff Member #{i+1}", expanded=False):
                        cols = st.columns(3)
                        name = cols[0].text_input(f"Name*", key=f"{staff_type}_name_{i}").strip()
                        gender = cols[1].selectbox("Gender*", ["Male", "Female"], key=f"{staff_type}_gender_{i}")
                        education = cols[2].selectbox("Highest Edu. Level*", education_options, key=f"{staff_type}_edu_{i}")
                        
                        if name:
                            name = self.format_name(name)
                        staff_data.append({
                            "name": name,
                            "gender": gender,
                            "education": education
                        })
            return staff_data

    def pupils_section(self):
        with st.container(border=True):
            st.subheader("Pupil Data by Class")
            class_levels = list(st.session_state.class_data.keys())
            
            for level in class_levels:
                with st.expander(level, expanded=False):
                    cols = st.columns(3)
                    males = cols[0].number_input("Males", min_value=0, key=f"{level}_males")
                    females = cols[1].number_input("Females", min_value=0, key=f"{level}_females")
                    tuition = cols[2].number_input("Tuition Fees (GHS)", min_value=0, key=f"{level}_tuition")
                    
                    st.session_state.class_data[level] = {
                        "males": males,
                        "females": females,
                        "tuition": tuition
                    }

    def financial_section(self):
        with st.container(border=True):
            st.subheader("Fees & Salaries")
            
            st.write("**Fees (GHS)**")
            col1, col2, col3 = st.columns(3)
            self.admission_fees = col1.number_input("Admission Fees*", min_value=0)
            self.canteen_fees = col2.number_input("Canteen Fees*", min_value=0)
            self.stationary_fees = col3.number_input("Stationary Fees*", min_value=0)
            
            st.write("**Salary Ranges (GHS)**")
            col4, col5, col6 = st.columns(3)
            self.head_salary = col4.number_input("Head Teacher Salary*", min_value=0)
            self.lowest_teacher_salary = col5.number_input("Lowest Teacher Salary*", min_value=0)
            self.highest_teacher_salary = col6.number_input("Highest Teacher Salary*", min_value=0)

    def committee_section(self):
        with st.container(border=True):
            st.subheader("School Management Committee")
            num_members = st.number_input(
                "Number of Committee Members*",
                min_value=0,
                max_value=20,
                step=1
            )
            
            committee_data = []
            if num_members > 0:
                st.write(f"**Enter details for {num_members} committee members:**")
                for i in range(num_members):
                    with st.expander(f"Committee Member #{i+1}", expanded=False):
                        cols = st.columns(2)
                        name = cols[0].text_input(f"Name*", key=f"committee_name_{i}").strip()
                        contact = cols[1].text_input(f"Contact*", key=f"committee_contact_{i}").strip()
                        
                        if name:
                            name = self.format_name(name)
                        committee_data.append({
                            "name": name,
                            "contact": contact
                        })
            return committee_data

    def validate_form(self):
        required_fields = [
            self.zone, self.region, self.division, 
            self.school_name, self.head_teacher
        ]
        
        if not all(required_fields):
            st.error("All required fields in School Information must be filled")
            return False
            
        if not self.validate_phone(self.phone):
            st.error("Valid 10-digit phone number required for Head Teacher")
            return False
            
        if not self.validate_phone(self.whatsapp):
            st.error("Valid 10-digit WhatsApp number required for Head Teacher")
            return False
            
        return True

    def flatten_data(self):
        """Flatten all data into a single row for Google Sheets"""
        # School information
        data = {
            "Zone": self.zone,
            "Region": self.region,
            "Division": self.division,
            "School Name": self.format_name(self.school_name),
            "Head Teacher": self.format_name(self.head_teacher),
            "Phone": self.phone,
            "WhatsApp": self.whatsapp,
        }
        
        # Teaching staff
        for i, staff in enumerate(st.session_state.teaching_staff, 1):
            data.update({
                f"Teaching Staff {i} Name": staff["name"],
                f"Teaching Staff {i} Gender": staff["gender"],
                f"Teaching Staff {i} Education": staff["education"]
            })
        
        # Non-teaching staff
        for i, staff in enumerate(st.session_state.non_teaching_staff, 1):
            data.update({
                f"Non-Teaching Staff {i} Name": staff["name"],
                f"Non-Teaching Staff {i} Gender": staff["gender"],
                f"Non-Teaching Staff {i} Education": staff["education"]
            })
        
        # Class data
        for level, values in st.session_state.class_data.items():
            data.update({
                f"{level} Males": values["males"],
                f"{level} Females": values["females"],
                f"{level} Tuition": values["tuition"]
            })
        
        # Financial data
        financial_data = {
            "Admission Fees": self.admission_fees,
            "Canteen Fees": self.canteen_fees,
            "Stationary Fees": self.stationary_fees,
            "Head Teacher Salary": self.head_salary,
            "Lowest Teacher Salary": self.lowest_teacher_salary,
            "Highest Teacher Salary": self.highest_teacher_salary
        }
        data.update(financial_data)
        
        # Committee members
        for i, member in enumerate(st.session_state.committee_members, 1):
            data.update({
                f"Committee Member {i} Name": member["name"],
                f"Committee Member {i} Contact": member["contact"]
            })
        
        return data

    def submit_data(self):
        try:
            # Get all flattened data
            data = self.flatten_data()
            
            client = cred()
            spreadsheet = client.open("DL Schools")
            worksheet = spreadsheet.worksheet("DL")
            
            # Append all data as a single row
            worksheet.append_row(list(data.values()))
            st.success("✅ Data submitted successfully!")
            st.balloons()
            
        except Exception as e:
            st.error(f"Submission failed: {str(e)}")

    def run(self):
        st.subheader("Deeper Life Basic Schools")
               
        try:
            client = cred()
            spreadsheet = client.open("DL Schools")
            worksheet = spreadsheet.worksheet("DL")
            st.success("✅ Network Active!")
        except:
            st.warning("⚠️ Network connection issue detected")
        
        self.school_info_section()
        
        teaching_education = ["HND", "Diploma", "Masters", "PhD", "WASSCE", "SSCE", "O'Level", "A'Level"]
        st.session_state.teaching_staff = self.staff_section("teaching", teaching_education)
        
        non_teaching_education = ["HND", "Diploma", "WASSCE", "SSCE", "O'Level", "A'Level", 
                                 "Certificate", "JHS", "No School"]
        st.session_state.non_teaching_staff = self.staff_section("non_teaching", non_teaching_education)
        
        self.pupils_section()
        self.financial_section()
        st.session_state.committee_members = self.committee_section()
        
        if st.button("Submit Data", type="primary"):
            if self.validate_form():
                self.submit_data()


if __name__ == "__main__":
    DeeperLifeSurvey()
   