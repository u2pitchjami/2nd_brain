PROMPTS = {
    "technical": """
    You are an intelligent note-organizing assistant.
    Your task is to summarize the following technical article.
    Provide a comprehensive summary that captures the main ideas, key findings, and essential technical details.
    Structure your summary logically, starting with an overview and progressing through the article's main sections.
    Use markdown to format your output, bolding key subject matter and potential areas that may need expanded information.
    Ensure the summary is accessible to the target audience while maintaining technical accuracy.
    Conclude with the most significant implications or applications of the article's content.
    The output must be in **French**, presented in **Markdown format**, and must **avoid unnecessary introductory or concluding phrases**.
            Here is the text :
            {content}
            """,
    "news": """
    You are an intelligent note-organizing assistant.
    Your task is to summarize the following article.
    Provide a comprehensive summary that captures the main ideas, key findings.
    Structure your summary logically, starting with an overview and progressing through the article's main sections.
    Use markdown to format your output, bolding key subject matter and potential areas that may need expanded information.
    Ensure the summary is accessible to the target audience while maintaining technical accuracy.
    Conclude with the most significant implications or applications of the article's content.
    The output must be in **French**, presented in **Markdown format**, and must **avoid unnecessary introductory or concluding phrases**.
            Here is the text :
            {content}
            """,
    "idea": """
    Provide a comprehensive summary and structured outline of [topic/project].
    Include the following elements:
        - A concise overview in 2-3 sentences
        - Key objectives or goals
        - Main ideas or components, organized into logical sections
        - Reflections on challenges, insights, and lessons learned
        - Potential next steps or areas for improvement
        - Format the response using appropriate headers, bullet points, and numbering.
        - Ensure the summary is clear, concise, and captures the essential elements without excessive detail.
        - The output must be in **French**, presented in **Markdown format**, and must **avoid unnecessary introductory or concluding phrases**.
            Here is the text :
            {content}
            """,
    "todo": """
    You are an intelligent note-organizing assistant.
    Create a comprehensive task management plan that:
        - Prioritizes tasks using a strategic approach
        - Allocates appropriate time blocks
        - Identifies potential bottlenecks
        - Suggests optimal task sequencing

        - Current tasks: [detailed task list]
        - Project goals: [specific objectives]
        - Time constraints: [available working hours]
    The output must be in **French**, presented in **Markdown format**, and must **avoid unnecessary introductory or concluding phrases**.
            Here is the text :
            {content}
            """,
    "tutorial": """
    You are an intelligent note-organizing assistant.
    Please reorganize the tutorial to enhance its clarity and user engagement.
    Start by reviewing the current structure and content.
    Identify any sections that need to be reordered, combined, or split.
    Ensure that each section begins with a clear introduction, followed by a detailed explanation, and ends with practical examples or exercises.
    Highlight the key points and the key commands.
    Provide a revised outline of the tutorial with suggested changes.
    suggests ways to explore the subject in more depth
    The output must be in **French**, presented in **Markdown format**, and must **avoid unnecessary introductory or concluding phrases**.
            Here is the text :
            {content}
            """,            
    "title": """
    You are an intelligent note-organizing assistant. Add clear, structured titles in markdown format.

    **Instructions:**
    - Use `##` for major sections.
    - Use `###` for subsections within each section.
    - Use `####` only for deeply detailed points.
    - Do not add unnecessary titles like "ChatGPT said" or "You said".
    - Titles should be short (max 8 words) and descriptive.
    - The output must be in **French**, presented in **Markdown format**, and must **avoid unnecessary introductory or concluding phrases**.
  

    Here is the text to process:
    {content}    
    """,
    "tags": """
    You are a bot in a read-it-later app and your responsibility is to help with automatic tagging.
    Please analyze the text between the sentences "CONTENT START HERE" and "CONTENT END HERE" and suggest relevant tags that describe its key themes, topics, and main ideas. The rules are:
    - Aim for a variety of tags, including broad categories, specific keywords, and potential sub-genres.
    - The tags language must be in English.
    - If it's a famous website you may also include a tag for the website. If the tag is not generic enough, don't include it.
    - The content can include text for cookie consent and privacy policy, ignore those while tagging.
    - Aim for 3-5 tags.
    - if a specific hardware and/or specific software are use add tags with the names for each.
    - If there are no good tags, leave the array empty.
    
    CONTENT START HERE
    {content}
    CONTENT END HERE
    
    Respond in JSON with the key "tags" and the value as an array of string tags.
    """,
    "summary": """
    Provide a concise summary of the key points discussed in the following text.
    Focus on the main arguments, supporting evidence, and any significant conclusions.
    Present the summary in a bullet-point format, highlighting the most crucial information.
    The summary should not be longer than 5 sentences. 
    **without including the parts already present** in the "summary:" section. Do not repeat existing elements
    
    TEXT START
    {content}
    TEXT END
    """,
    "synthese": """
    You are an intelligent note-organizing assistant. Analyze the following content and add clear, structured titles in markdown format
    1. Identify the main topic of the text.
    2. List the key supporting points.
    3. Present the summary in a bullet-point format, highlighting the most crucial information.
    4. Highlight any important data or statistics.
    5. The output must be in **French**, presented in **Markdown format**, and must **avoid unnecessary introductory or concluding phrases**.
Here is the text to process:
    {content}    
    """,
    "synthese2": """
    You are an intelligent note-organizing assistant.
    the content is a synthesis recomposed from several blocks.
    your goal is to :
        - structure the text logically, using clear paragraphs.
        - Connect important ideas
        - Remove superfluous or redundant details.
        - Make sure the result is fluid and readable.
        - Capture the author's conclusion or main argument.
        - Synthesize the information into a concise summary.
        - Ends with 1-2 reflection questions to explore the topic further
        - The output must be in **French**, presented in **Markdown format**, and must **avoid unnecessary introductory or concluding phrases**.
    Here is the text to process:
    {content}    
    """,
    "type": """
You are an intelligent note-organizing assistant.
Your task is to classify the following content into one of the categories below.
Choose the most appropriate type based on the main purpose or structure of the text.
Only select "unknown" if absolutely no other category fits.

Categories (with examples):
- "technical": A technical article or document, e.g., a software guide, API documentation, or white paper.
- "news": General information or current events, e.g., a news report or blog post about world affairs.
- "idea": A text that proposes ideas, thoughts, or project outlines, e.g., a brainstorming note or concept description.
- "todo": A to-do list or text with actionable tasks, e.g., a grocery list or project checklist.
- "tutorial": A step-by-step guide or lesson, e.g., a programming tutorial or recipe.
- "unknown": Use this only if the text does not fit into any of the above categories.

Returns only this word without any further explanatory text.
Text to analyze:
{content}
"""
   
   
   
   
   
   
    
    
}