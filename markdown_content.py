sidebar_markdown = """
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
            
    [data-testid=stSidebar] {
        background-color: #ECF1F5;
            
    }                    
    .stDeployButton {
            visibility: hidden;
        }
</style>
"""

main_container_css ="""
<style>
#MainMenu {visibility: hidden;}
.stAppDeployButton {display:none;}
 
.block-container
{
    padding-top: 0rem;
    padding-bottom: 0rem;
    margin-top: 0rem;
} 
</style>
"""

# CSS for layout and styling
layout_css = """
    <style>
    .container {
        display: flex;
        justify-content: center; /* Center align the container contents */
        align-items: center;
        width: 100%;
        margin-bottom: 0; /* Remove margin below the container */
    }
    .title {
        text-align: center;
        margin: 0; /* Remove default margin */
        flex-grow: 1; /* Allow the title to take up available space */
    }
    .title h1 {
        font-size: 30px; /* Set the font size of the title */
        color: #1E2247; /* Set the color of the title */
        margin: 0; /* Remove default margin */
        font-family: Arial, sans-serif; /* Set the font to Arial */
        margin-bottom: -0.5rem
    }
    .image-container {
        flex-shrink: 0; /* Prevent the image from shrinking */
        margin-left: 10px; /* Add some space between the title and the image */
    }
    .image {
        width: 100px; /* Adjust the width as needed */
    }
    hr {
        margin-top: 0; /* Remove margin above the horizontal line */
        border: none; /* Remove the default border */
        height: 10px; /* Set the height of the line */
        background-color: #1E2247; /* Set the color of the line */
    }
    </style>
    """

def generate_title_image_markdown(img_str,project_name):
    return f"""
    <div class="container">
        <div class="title">
            <h1>{project_name}</h1>
        </div>
        <div class="image-container">
            <img src="data:image/png;base64,{img_str}" class="image">
        </div>
    </div>
    <hr>
    """