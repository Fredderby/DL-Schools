import streamlit as st
import pandas as pd
import re
import datetime
from connect import cred
import gspread
from google.auth.exceptions import RefreshError, TransportError


class DeeperLifeSurvey:
    def __init__(self):
        self.initialize_session_state()
        
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
        # Page navigation
        if "current_page" not in st.session_state:
            st.session_state.current_page = 1
            
        # Form validation
        if "basic_info_valid" not in st.session_state:
            st.session_state.basic_info_valid = False
        if "pupil_data_valid" not in st.session_state:
            st.session_state.pupil_data_valid = False
        if "financial_data_valid" not in st.session_state:
            st.session_state.financial_data_valid = False
        if "staff_counts_valid" not in st.session_state:
            st.session_state.staff_counts_valid = False
            
        # Form data
        if "school_info" not in st.session_state:
            st.session_state.school_info = {
                "zone": None,
                "region": None,
                "division": None,
                "school_name": "",
                "head_teacher": "",
                "phone": "",
                "whatsapp": ""
            }
            
        if "staff_counts" not in st.session_state:
            st.session_state.staff_counts = {
                "teaching_staff_count": 0,
                "non_teaching_staff_count": 0,
                "committee_members_count": 0
            }
            
        if "financial_data" not in st.session_state:
            st.session_state.financial_data = {
                "admission_fees": 0,
                "canteen_fees": 0,
                "stationary_fees": 0,
                "head_salary": 0,
                "lowest_teacher_salary": 0,
                "highest_teacher_salary": 0
            }
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

    def check_duplicate_entry(self):
        """Check if the headmaster's details already exist in the database"""
        try:
            client = cred()
            spreadsheet = client.open("DL Schools")
            worksheet = spreadsheet.worksheet("DL")
            
            # Get all existing data
            existing_data = worksheet.get_all_records()
            
            # Check for duplicates based on headmaster name, phone, whatsapp, region, and division
            formatted_head_teacher = self.format_name(st.session_state.school_info["head_teacher"])
            
            for record in existing_data:
                if (record.get("Head Teacher", "") == formatted_head_teacher and
                    record.get("Phone", "") == st.session_state.school_info["phone"] and
                    record.get("WhatsApp", "") == st.session_state.school_info["whatsapp"] and
                    record.get("Region", "") == st.session_state.school_info["region"] and
                    record.get("Division", "") == st.session_state.school_info["division"]):
                    return True
            return False
        except Exception as e:
            st.error(f"Error checking for duplicates: {str(e)}")
            return False

    def school_info_section(self):
        with st.container(border=True):
            st.subheader("Basic Information")

            zones = self.df['ZONE'].unique()
            st.session_state.school_info["zone"] = st.selectbox(
                "Zone*", 
                options=zones, 
                index=None, 
                placeholder="Select a zone...",
                key="zone_select"
            )

            if st.session_state.school_info["zone"]:
                regions = self.df[self.df['ZONE'] == st.session_state.school_info["zone"]]['REGION'].unique()
                st.session_state.school_info["region"] = st.selectbox(
                    "Region*", 
                    options=regions, 
                    index=None, 
                    placeholder="Select a region...",
                    key="region_select"
                )

            if st.session_state.school_info["region"]:
                divisions = self.df[self.df['REGION'] == st.session_state.school_info["region"]]['DIVISION'].unique()
                st.session_state.school_info["division"] = st.selectbox(
                    "Division*", 
                    options=divisions, 
                    index=None, 
                    placeholder="Select a division...",
                    key="division_select"
                )

            st.session_state.school_info["school_name"] = st.text_input(
                "Name of School*", 
                max_chars=100,
                value=st.session_state.school_info["school_name"]
            ).strip()
            
            st.session_state.school_info["head_teacher"] = st.text_input(
                "Name of Head Teacher*", 
                max_chars=100,
                value=st.session_state.school_info["head_teacher"]
            ).strip()
            
            col1, col2 = st.columns(2)
            st.session_state.school_info["phone"] = col1.text_input(
                "Phone Number of Head Teacher*", 
                max_chars=10,
                value=st.session_state.school_info["phone"]
            )
            
            st.session_state.school_info["whatsapp"] = col2.text_input(
                "WhatsApp Number of Head Teacher*", 
                max_chars=10,
                value=st.session_state.school_info["whatsapp"]
            )
            
            if st.session_state.school_info["phone"] and not self.validate_phone(st.session_state.school_info["phone"]):
                col1.error("Must be 10 digits")
            if st.session_state.school_info["whatsapp"] and not self.validate_phone(st.session_state.school_info["whatsapp"]):
                col2.error("Must be 10 digits")

    def pupils_section(self):
        with st.container(border=True):
            st.subheader("Pupil Data by Class")
            class_levels = list(st.session_state.class_data.keys())
            
            for level in class_levels:
                with st.expander(level, expanded=False):
                    cols = st.columns(3)
                    males = cols[0].number_input("Males*", min_value=0, key=f"{level}_males")
                    females = cols[1].number_input("Females*", min_value=0, key=f"{level}_females")
                    tuition = cols[2].number_input("Tuition Fees (GHS)*", min_value=0, key=f"{level}_tuition")
                    
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
            st.session_state.financial_data["admission_fees"] = col1.number_input(
                "Admission Fees*", 
                min_value=0, 
                value=st.session_state.financial_data["admission_fees"],
                key="admission_fees"
            )
            
            st.session_state.financial_data["canteen_fees"] = col2.number_input(
                "Canteen Fees*", 
                min_value=0, 
                value=st.session_state.financial_data["canteen_fees"],
                key="canteen_fees"
            )
            
            st.session_state.financial_data["stationary_fees"] = col3.number_input(
                "Stationary Fees*", 
                min_value=0, 
                value=st.session_state.financial_data["stationary_fees"],
                key="stationary_fees"
            )
            
            st.write("**Salary Ranges (GHS)**")
            col4, col5, col6 = st.columns(3)
            st.session_state.financial_data["head_salary"] = col4.number_input(
                "Head Teacher Salary*", 
                min_value=0, 
                value=st.session_state.financial_data["head_salary"],
                key="head_salary"
            )
            
            st.session_state.financial_data["lowest_teacher_salary"] = col5.number_input(
                "Lowest Teacher Salary*", 
                min_value=0, 
                value=st.session_state.financial_data["lowest_teacher_salary"],
                key="lowest_salary"
            )
            
            st.session_state.financial_data["highest_teacher_salary"] = col6.number_input(
                "Highest Teacher Salary*", 
                min_value=0, 
                value=st.session_state.financial_data["highest_teacher_salary"],
                key="highest_salary"
            )

    def staff_counts_section(self):
        with st.container(border=True):
            st.subheader("Staff Counts")
            
            col1, col2, col3 = st.columns(3)
            
            st.session_state.staff_counts["teaching_staff_count"] = col1.number_input(
                "Number of Teaching Staff*",
                min_value=0,
                max_value=100,
                step=1,
                key="teaching_staff_count"
            )
            
            st.session_state.staff_counts["non_teaching_staff_count"] = col2.number_input(
                "Number of Non-Teaching Staff*",
                min_value=0,
                max_value=100,
                step=1,
                key="non_teaching_staff_count"
            )
            
            st.session_state.staff_counts["committee_members_count"] = col3.number_input(
                "Number of Committee Members*",
                min_value=0,
                max_value=50,
                step=1,
                key="committee_members_count"
            )

    def validate_basic_info(self):
        required_fields = [
            st.session_state.school_info["zone"], 
            st.session_state.school_info["region"], 
            st.session_state.school_info["division"], 
            st.session_state.school_info["school_name"], 
            st.session_state.school_info["head_teacher"],
            st.session_state.school_info["phone"],
            st.session_state.school_info["whatsapp"]
        ]
        
        if not all(required_fields):
            st.error("All required fields in School Information must be filled")
            return False
            
        if not self.validate_phone(st.session_state.school_info["phone"]):
            st.error("Valid 10-digit phone number required for Head Teacher")
            return False
            
        if not self.validate_phone(st.session_state.school_info["whatsapp"]):
            st.error("Valid 10-digit WhatsApp number required for Head Teacher")
            return False
        
        # Check for duplicate entry
        if self.check_duplicate_entry():
            st.error("This headmaster's information already exists in the database for this region and division.")
            return False
            
        return True

    def validate_pupil_data(self):
        # Check if all classes have data
        for level, values in st.session_state.class_data.items():
            if values["males"] == 0 and values["females"] == 0 and values["tuition"] == 0:
                st.error(f"Pupil Data is required for {level}. Please enter data for all classes.")
                return False
                
        return True

    def validate_financial_data(self):
        # Check if all financial fields are filled
        required_financial_fields = [
            st.session_state.financial_data["admission_fees"],
            st.session_state.financial_data["canteen_fees"],
            st.session_state.financial_data["stationary_fees"],
            st.session_state.financial_data["head_salary"],
            st.session_state.financial_data["lowest_teacher_salary"],
            st.session_state.financial_data["highest_teacher_salary"]
        ]
        
        if not all(required_financial_fields):
            st.error("All financial fields are required.")
            return False
            
        return True

    def validate_staff_counts(self):
        # Check if all staff count fields are filled
        required_staff_fields = [
            st.session_state.staff_counts["teaching_staff_count"],
            st.session_state.staff_counts["non_teaching_staff_count"],
            st.session_state.staff_counts["committee_members_count"]
        ]
        
        if not all(required_staff_fields):
            st.error("All staff count fields are required.")
            return False
            
        return True

    def next_page_callback(self):
        if st.session_state.current_page == 1:
            if self.validate_basic_info():
                st.session_state.basic_info_valid = True
                st.session_state.current_page = 2
        elif st.session_state.current_page == 2:
            if self.validate_pupil_data():
                st.session_state.pupil_data_valid = True
                st.session_state.current_page = 3

    def prev_page_callback(self):
        if st.session_state.current_page > 1:
            st.session_state.current_page -= 1

    def flatten_data(self):
        """Flatten all data into a single row for Google Sheets in the specified order"""
        data = {}
        
        # Add timestamp first
        data.update({
            "Timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # 1. Basic information
        data.update({
            "Zone": st.session_state.school_info["zone"],
            "Region": st.session_state.school_info["region"],
            "Division": st.session_state.school_info["division"],
            "School Name": self.format_name(st.session_state.school_info["school_name"]),
            "Head Teacher": self.format_name(st.session_state.school_info["head_teacher"]),
            "Phone": st.session_state.school_info["phone"],
            "WhatsApp": st.session_state.school_info["whatsapp"],
        })
        
        # 2. Pupil Data by Class
        for level, values in st.session_state.class_data.items():
            data.update({
                f"{level} Males": values["males"],
                f"{level} Females": values["females"],
                f"{level} Tuition": values["tuition"]
            })
        
        # 3. Fees and Salaries
        data.update({
            "Admission Fees": st.session_state.financial_data["admission_fees"],
            "Canteen Fees": st.session_state.financial_data["canteen_fees"],
            "Stationary Fees": st.session_state.financial_data["stationary_fees"],
            "Head Teacher Salary": st.session_state.financial_data["head_salary"],
            "Lowest Teacher Salary": st.session_state.financial_data["lowest_teacher_salary"],
            "Highest Teacher Salary": st.session_state.financial_data["highest_teacher_salary"]
        })
        
        # 4. Staff counts
        data.update({
            "Number of Teaching Staff": st.session_state.staff_counts["teaching_staff_count"],
            "Number of Non-Teaching Staff": st.session_state.staff_counts["non_teaching_staff_count"],
            "Number of Committee Members": st.session_state.staff_counts["committee_members_count"]
        })
        
        return data

    def submit_data(self):
        try:
            # Validate all sections before submission
            if not (self.validate_basic_info() and self.validate_pupil_data() and 
                   self.validate_financial_data() and self.validate_staff_counts()):
                st.error("Please complete all required fields before submitting.")
                return
                
            # Get all flattened data
            data = self.flatten_data()
            
            client = cred()
            spreadsheet = client.open("DL Schools")
            worksheet = spreadsheet.worksheet("DL")
            
            # Check if the sheet is empty (no headers)
            existing_data = worksheet.get_all_values()
            if len(existing_data) == 0:
                # Add headers as the first row
                headers = list(data.keys())
                worksheet.append_row(headers)
            
            # Append all data as a single row
            worksheet.append_row(list(data.values()))
            st.success("✅ Data submitted successfully!")
            st.balloons()
            
        except Exception as e:
            st.error(f"Submission failed: {str(e)}")

    def page_one(self):
        """First page with Basic Information"""
        st.subheader("Deeper Life Basic Schools - Page 1/3")
        
        try:
            client = cred()
            spreadsheet = client.open("DL Schools")
            worksheet = spreadsheet.worksheet("DL")
            st.success("✅ Network Active!")
        except:
            st.warning("⚠️ Network connection issue detected")
        
        self.school_info_section()
        
        # Navigation buttons
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Previous", disabled=True):
                pass  # Disabled on first page
        with col2:
            if st.button("Next", type="primary", on_click=self.next_page_callback):
                pass

    def page_two(self):
        """Second page with Pupil Data"""
        st.subheader("Deeper Life Basic Schools - Page 2/3")
        
        self.pupils_section()
        
        # Navigation buttons
        col1, col2 = st.columns(2)
        with col1:
            st.button("Previous", on_click=self.prev_page_callback)
        with col2:
            st.button("Next", type="primary", on_click=self.next_page_callback)

    def page_three(self):
        """Third page with Financial Data and Staff Counts"""
        st.subheader("Deeper Life Basic Schools - Page 3/3")
        
        self.financial_section()
        self.staff_counts_section()
        
        # Add footnote about submitting detailed information
        st.markdown("---")
        st.info(
            "**Important Note:** Please submit the detailed lists of Committee members, "
            "Teaching staff, and Non-teaching staff (including their salaries, qualifications, "
            "and contact information) to the email: **dledu.director@dclmgh.org**"
        )
        
        # Navigation and submit buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            st.button("Previous", on_click=self.prev_page_callback)
        with col3:
            if st.button("Submit Data", type="primary"):
                self.submit_data()

    def run(self):
        """Main method to run the app with page navigation"""
        if st.session_state.current_page == 1:
            self.page_one()
        elif st.session_state.current_page == 2:
            self.page_two()
        elif st.session_state.current_page == 3:
            self.page_three()


if __name__ == "__main__":
    DeeperLifeSurvey()
  