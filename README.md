# NLP-Project
Due on the 11th of June. See attached description PDF for abstract.

### Project Goal
Briefly put, it's to build a website that asks for you to input an institution name  (in fields of Finance, Medicine, & Education), and with the use of LLMs, creates a profile for said instituion, ideally containing as much information as possible for those types of institutions

### Key Tasks
1) **Website UI & UX:**
    - [X] Should at least have an input form, loading animation & other forms of feedback, and a screen to show the output profile in a tidy way, which may vary by institution type
    - [X] Input can be supported by autocomplete (several option lists) and autocorrect with the use of prefix trees
    - [X] Output screen might include images or logos if found for the organisation
    - [X] Additional input options (like region or address, or explicit type of organisation) in case distinguishing by the name alone is not possible might need to be included as optional fields (with conditional visibility if necessary)
 
2) **Data Retrieval:**
    - [X] A custom query can be formed (especially if optional fields were specified) and used to search for initial documents either with search APIs, or if not possible some other way (like using google on a browser with selenium)
    - [X] Initial websites/docs then have to be crawled to visit all pages and download all the text 
    - [X] Relevant data then needs to be retrieved and the rest ignored, there are methods like RAG which decide which chunks of data are relevant and there's a lot of models that can be used for
    - [X] Relevance might need to be explicitly defined when saving data, like "does this text have the number of workers in the institution" when information is retrieved, in case we want the LLM to build some fields in the profile as a separate request, where a lot of information we give it would be useless

3) **Data Restructuring (The Core):**
    - X ] After all relevant data is retrieved it has to be restructured using the LLMs with prompt engineering, the output (& maybe input) structure could be JSON, XML, or [BAML](https://www.boundaryml.com/) which is less taxing and more resistant to errors
    - [X] Said restructuring needs to be through a pipeline that optimises the cost (less input and output tokens), speed (more small requests rather than one big one), and accuracy (prompt quality and amount and quality of data included)
      - [X] This means some fields can be populated through multiple prompts, or on their own prompt without asking for other fields.
      - [X] Summarising data first or separating it correctly (more throughly than RAG's chunks) might help with quality or speed further in the pipeline or in general
      - [X] Additional validation steps might make sense in some cases

4) **Response Parsing & Output:**
    - [X] LLM responses need to be parsed and turned to objects (JSON/XML/BAML parsers), or if no output structure was used, displayed as is on the website
    - [X] Fields that are empty or didn't pass validation and so on should be hidden or some error shown for that field

5) **Benchmarking & Accuracy Validation:**
    - [X] If we want to get the best grade and compare performing we should at least log cost and speed between methods or models or pipeline versions or whatever
    - [X] If there's a way to also check for accuracy or quality it'd be great



