# EcuapassDocs2-dev: Creation of Ecuapass Documents 
- Create cartas de porte, manifiestos, and declaraciones on line
- Save data to postgres DB.
- Custom user management

## LOG
Sep/05: r0.900 : Redesigned to use only one Document class including txt fields. Working basics

Aug/13: r0.859 : Moved to klnx
Mar/10: r0.858 : Added working dirs _doc and _dev

Oct/26: r0.857 : Working on Aldia scraping.
Oct/26: r0.856 : Fixed bot_migration: vehiculo : conductor. 
Oct/26: r0.855 : Predicting Manifiesto fields. 
Oct/22: r0.854 : Adding Manifiesto predictions. Modified Ecuapassdocs CPI, MCI, Utils
Oct/18: r0.853 : Testing predictions for CPI. Modified extractInfo: analysysType.
Oct/16: r0.852 : Working predictions for CPI, no testing. Create JS handler for prediction.
Oct/09: r0.850 : Improved vehiculo autocomplete: Added AUTOFIXED flag when handling maxlines.
Oct/07: r0.849 : Doc view with left sidebar using iframes. Removed default "fecha emision".
Oct/05: r0.848 : Added manifiesto association: vehiculo-remolque-conductor. Modified tables: manifiesto, vehiculo.
Sep/28: r0.847 : Working in cloud 'ecuapassdocs.app'. Update db process. Pagination.
Sep/23: r0.846 : Data loading (logitrans CPI/MCI/DTI). BYZA data upto 2021. Added detail to form.
Sep/19: r0.845 : Saved sorted CPI files to app.
Sep/18: r0.844 : Migration data: BYZA, LOGITRANS. Title for doc tabs.
Sep/16: r0.843 : Adjusted for 'bot_migration' (CPIs). migrationFields, 'referencia' field, setValues.
Sep/11: r0.841 : New general search and listing for docs and entities.
Sep/11: r0.840 : Working on Railway: 'Procfile' for statics. Ecuapasdocs as library (r0.85).
Sep/10: r0.838 : Removed lib ecuapassdocs. Added links to it.
Sep/10: r0.837 : Removed Procfile
Sep/10: r0.836 : Using PG Vars in settings
Sep/07: r0.834 : Replaces country form with CustomAuthForm. Changing external .css .js to local
Sep/03: r0.833 : Working Declaracion: Save/Autocomplete.
Sep/03: r0.832 : Fixing Declaracion options for manifiesto
Sep/03: r0.831 : Working Declaracion. One url file for options. New models_Scripts.
Sep/01: r0.830 : Working base class table for listing. Menu by doc instead by action.
Aug/30: r0.820 : Working bootstrap sidebar. Renamed files. User login/logout. Admin.
Aug/30: Added nice sidebar with content. No file renames yet.
Aug/24: Renamed Empresa to Cliente. Created listing_xxx for list docs. Renamed appdoc tod app_doc.
Aug/23: r0.51 : Working EC, CO, PE for CPI, MCI, DTI. Added user, pais. Font courier mono.
Aut/16: r0.501: Redesigned to use onCommandFunctions in POST and GET.
Aug/11: Working Manifiesto optionsView (.., cartaporte)
Aug/06: Reorganizing code for menus. Menus uses only one function. POST request to GET request.
