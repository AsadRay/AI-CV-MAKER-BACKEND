# import os
# import subprocess
# import uuid

# TEMPLATE_DIR = "app/latex_templates"
# OUTPUT_DIR = "generated_cvs"

# os.makedirs(OUTPUT_DIR, exist_ok=True)


# def latex_escape(text):
#     if not text:
#         return ""

#     replacements = {
#         "&": r"\&",
#         "%": r"\%",
#         "$": r"\$",
#         "#": r"\#",
#         "_": r"\_",
#         "{": r"\{",
#         "}": r"\}",
#         "~": r"\textasciitilde{}",
#         "^": r"\textasciicircum{}",
#         "\\": r"\textbackslash{}",
#     }

#     for char, replacement in replacements.items():
#         text = text.replace(char, replacement)

#     return text


# def render_tex(cv_data, template_name):
#     """Render CV data into LaTeX template"""
    
#     # Load template
#     template_path = os.path.join(TEMPLATE_DIR, f"{template_name}.tex")
    
#     if not os.path.exists(template_path):
#         raise FileNotFoundError(f"Template not found: {template_name}")
    
#     with open(template_path, "r", encoding="utf-8") as f:
#         template = f.read()
    
#     # Extract data
#     personal = cv_data.get("personal_info", {})
#     education = cv_data.get("education", [])
#     experience = cv_data.get("experience", [])
#     skills = cv_data.get("skills", [])
#     projects = cv_data.get("projects", [])
    
#     # Build header block
#     name = latex_escape(personal.get("name", ""))
#     email = latex_escape(personal.get("email", ""))
#     phone = latex_escape(personal.get("phone", ""))
#     location = latex_escape(personal.get("location", ""))
    
#     # ✅ Use regular strings, not f-strings, to avoid brace confusion
#     header_block = "{\\Huge\\bfseries\\color{primary} " + name + "}\\\\[0.2cm]\n"
    
#     contact_parts = []
#     if email:
#         contact_parts.append("\\href{mailto:" + email + "}{" + email + "}")
#     if phone:
#         contact_parts.append(phone)
#     if location:
#         contact_parts.append(location)
    
#     if contact_parts:
#         header_block += "{\\large\\color{lightgray} " + " $\\bullet$ ".join(contact_parts) + "}\n"
    
#     # Build education block
#     education_block = ""
#     for edu in education:
#         degree = latex_escape(edu.get("degree", ""))
#         institution = latex_escape(edu.get("institution", ""))
#         year = str(edu.get("graduation_year", ""))
#         gpa = latex_escape(edu.get("gpa", ""))
        
#         education_block += "\\subsection*{" + degree + "}\n"
#         education_block += "{\\color{lightgray} " + institution + " \\hfill " + year + "}\\\\[0.1cm]\n"
#         education_block += "GPA: " + gpa + "\\\\[0.3cm]\n"
    
#     # Build experience block
#     experience_block = ""
#     for exp in experience:
#         title = latex_escape(exp.get("title", ""))
#         company = latex_escape(exp.get("company", ""))
#         years = latex_escape(exp.get("years_experience", ""))
#         summary = latex_escape(exp.get("summary", ""))
        
#         experience_block += "\\subsection*{" + title + "}\n"
#         experience_block += "{\\color{lightgray} " + company + " \\hfill " + years + "}\\\\[0.1cm]\n"
#         experience_block += summary + "\\\\[0.3cm]\n"
    
#     # Build skills block
#     skills_block = ""
#     # Group skills into rows of 5
#     for i in range(0, len(skills), 5):
#         skill_group = skills[i:i+5]
#         skills_text = " $\\bullet$ ".join([latex_escape(skill) for skill in skill_group])
#         skills_block += skills_text + "\\\\\n"
    
#     # Build projects block
#     projects_block = ""
#     for project in projects:
#         project_name = latex_escape(project.get("name", ""))
#         description = latex_escape(project.get("description", ""))
#         techs = ", ".join([latex_escape(t) for t in project.get("technologies", [])])
        
#         projects_block += "\\subsection*{" + project_name + "}\n"
#         projects_block += description + "\\\\[0.1cm]\n"
#         projects_block += "{\\color{lightgray} \\textit{Technologies:} " + techs + "}\\\\[0.3cm]\n"
    
#     # Replace placeholders
#     template = template.replace("{header_block}", header_block)
#     template = template.replace("{education_block}", education_block)
#     template = template.replace("{experience_block}", experience_block)
#     template = template.replace("{skills_block}", skills_block)
#     template = template.replace("{projects_block}", projects_block)
    
#     # Generate unique filename
#     file_id = str(uuid.uuid4())
#     tex_path = os.path.join(OUTPUT_DIR, f"{file_id}.tex")
    
#     # Write to file
#     with open(tex_path, "w", encoding="utf-8") as f:
#         f.write(template)
    
#     return tex_path


# def compile_pdf(tex_path):
#     """Compile LaTeX to PDF using pdflatex"""
    
#     result = subprocess.run(
#         [
#             "pdflatex",
#             "-interaction=nonstopmode",
#             "-halt-on-error",
#             "-output-directory",
#             OUTPUT_DIR,
#             tex_path,
#         ],
#         stdout=subprocess.PIPE,
#         stderr=subprocess.PIPE,
#         text=True,
#     )
    
#     if result.returncode != 0:
#         print("LATEX ERROR:")
#         print(result.stdout)
#         print(result.stderr)
#         raise Exception("LaTeX compilation failed")
    
#     return tex_path.replace(".tex", ".pdf")


# def get_available_templates():
#     """List all available templates"""
#     templates = []
    
#     if not os.path.exists(TEMPLATE_DIR):
#         return templates
    
#     for file in os.listdir(TEMPLATE_DIR):
#         if file.endswith(".tex"):
#             template_name = file.replace(".tex", "")
#             templates.append({
#                 "name": template_name,
#                 "display_name": template_name.replace("_", " ").title()
#             })
    
#     return templates