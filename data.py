import streamlit as st
import pandas as pd
import re
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
            
        if "teaching_staff" not in st.session_state:
            st.session_state.teaching_staff = []
        if "non_teaching_staff" not in st.session_state:
            st.session_state.non_teaching_staff = []
        if "committee_members" not in st.session_state:
            st.session_state.committee_members = []
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

    def staff_section(self, staff_type, education_options, max_value=50):
        with st.container(border=True):
            st.subheader(f"{staff_type.replace('_', ' ').title()} Staff")
            num_staff_key = f"{staff_type}_count"
            
            if num_staff_key not in st.session_state:
                st.session_state[num_staff_key] = 0
                
            st.session_state[num_staff_key] = st.number_input(
                f"Number of {staff_type.replace('_', ' ')} Staff*",
                min_value=0,
                max_value=max_value,
                step=1,
                key=f"{staff_type}_num_input"
            )
            
            staff_data = []
            if st.session_state[num_staff_key] > 0:
                st.write(f"**Enter details for {st.session_state[num_staff_key]} {staff_type.replace('_', ' ')} staff:**")
                for i in range(st.session_state[num_staff_key]):
                    with st.expander(f"Staff Member #{i+1}", expanded=False):
                        cols = st.columns(3)
                        name = cols[0].text_input(f"Name*", key=f"{staff_type}_name_{i}").strip()
                        gender = cols[1].selectbox(
                            "Gender*", 
                            ["Male", "Female"], 
                            index=None,
                            key=f"{staff_type}_gender_{i}"
                        )
                        education = cols[2].selectbox(
                            "Highest Edu. Level*", 
                            education_options, 
                            index=None,
                            key=f"{staff_type}_edu_{i}"
                        )
                        
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

    def committee_section(self):
        with st.container(border=True):
            st.subheader("School Management Committee")
            
            if "committee_count" not in st.session_state:
                st.session_state.committee_count = 0
                
            st.session_state.committee_count = st.number_input(
                "Number of Committee Members*",
                min_value=0,
                max_value=20,
                step=1,
                key="committee_count_input"
            )
            
            committee_data = []
            if st.session_state.committee_count > 0:
                st.write(f"**Enter details for {st.session_state.committee_count} committee members:**")
                for i in range(st.session_state.committee_count):
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

    def validate_basic_info(self):
        required_fields = [
            st.session_state.school_info["zone"], 
            st.session_state.school_info["region"], 
            st.session_state.school_info["division"], 
            st.session_state.school_info["school_name"], 
            st.session_state.school_info["head_teacher"]
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
            
        return True

    def flatten_data(self):
        """Flatten all data into a single row for Google Sheets in the specified order"""
        data = {}
        
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
        
        # 4. School Management committees
        for i, member in enumerate(st.session_state.committee_members, 1):
            data.update({
                f"Committee Member {i} Name": member["name"],
                f"Committee Member {i} Contact": member["contact"]
            })
        
        # 5. Teaching staffs
        for i, staff in enumerate(st.session_state.teaching_staff, 1):
            data.update({
                f"Teaching Staff {i} Name": staff["name"],
                f"Teaching Staff {i} Gender": staff["gender"],
                f"Teaching Staff {i} Education": staff["education"]
            })
        
        # 6. Non-teaching staffs
        for i, staff in enumerate(st.session_state.non_teaching_staff, 1):
            data.update({
                f"Non-Teaching Staff {i} Name": staff["name"],
                f"Non-Teaching Staff {i} Gender": staff["gender"],
                f"Non-Teaching Staff {i} Education": staff["education"]
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

    def page_one(self):
        """First page with Basic Information and Teaching Staff"""
        st.subheader("Deeper Life Basic Schools")
        
        try:
            client = cred()
            spreadsheet = client.open("DL Schools")
            worksheet = spreadsheet.worksheet("DL")
            st.success("✅ Network Active!")
        except:
            st.warning("⚠️ Network connection issue detected")
        
        self.school_info_section()
        
        teaching_education = ["HND", "Diploma", "Masters", "PhD", "Bachelor", "WASSCE", "SSCE", "O'Level", "A'Level"]
        st.session_state.teaching_staff = self.staff_section("teaching", teaching_education)
        
        # Next page button
        if st.button("Next", type="primary"):
            if self.validate_basic_info():
                st.session_state.current_page = 2
                st.rerun()

    def page_two(self):
        """Second page with all other sections"""
        st.subheader("Deeper Life Basic Schools - Additional Information")
        
        # Previous page button
        if st.button("Previous"):
            st.session_state.current_page = 1
            st.rerun()
        
        non_teaching_education = ["Bachelor", "HND", "Diploma", "WASSCE", "SSCE", "O'Level", "A'Level", 
                                 "Certificate", "JHS", "No School"]
        st.session_state.non_teaching_staff = self.staff_section("non_teaching", non_teaching_education)
        
        self.pupils_section()
        self.financial_section()
        st.session_state.committee_members = self.committee_section()
        
        if st.button("Submit Data", type="primary"):
            self.submit_data()

    def run(self):
        """Main method to run the app with page navigation"""
        if st.session_state.current_page == 1:
            self.page_one()
        elif st.session_state.current_page == 2:
            self.page_two()


if __name__ == "__main__":
    DeeperLifeSurvey()
    