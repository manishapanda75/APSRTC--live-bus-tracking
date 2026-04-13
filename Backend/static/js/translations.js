const translations = {
  en: {
    // Shared / Header
    app_title: "APSRTC Live",
    app_subtitle: "Visakhapatnam Bus Tracker",
    navigation: "NAVIGATION",
    search_buses: "Search Buses",
    live_tracking: "Live Tracking",
    full_schedule: "Full Schedule",
    admin_panel: "Admin Panel",
    driver_portal: "Driver Portal",
    logout: "Logout",
    login: "Login",
    welcome_back: "Welcome Back",
    login_sub: "Login to track your bus live",
    username: "Username",
    password: "Password",
    remember_me: "Remember me for 30 days",
    new_user: "New user? Create Account",
    choose_username: "Choose Username",
    choose_password: "Create Password",
    create_account: "Create Account",
    have_account: "Already have an account? Login",

    // Search Section
    search_title: "Find Your Bus",
    search_subtitle: "Visakhapatnam APSRTC — Real-time schedules from RTC Complex",
    from: "From",
    to: "To",
    departure: "Departure",
    arrival: "Arrival",
    duration: "Duration",
    bus_type: "Bus Type",
    search_btn: "Search",
    all_destinations: "All Destinations",
    all_types: "All Types",
    results_title: "Search Results",
    no_results: "No buses found",
    no_results_sub: "Try a different destination or bus type",
    select_dest_prompt: "Select a destination to view buses",
    fare: "Fare",
    departs: "Departs",
    arrives: "Arrives",
    next_bus_in: "Next bus in",
    running: "Running",
    found: "found",
    buses: "buses",
    bus: "bus",
    next_in: "Next in",
    departing_now: "Departing now!",
    departing_soon: "Departing soon!",
    min: "min",
    search_placeholder: "Search destination or route...",

    // Schedule Table
    col_route: "ROUTE",
    col_destination: "DESTINATION",
    col_type: "TYPE",
    col_departs: "DEPARTS",
    col_arrives: "ARRIVES",
    col_duration: "DURATION",
    col_fare: "FARE",
    col_next_bus: "NEXT BUS",
    full_schedule_heading: "Full Schedule",

    // Bus Types
    metro_express: "Metro Express",
    express: "Express",
    ordinary: "Ordinary",

    // Live Tracking
    live_title: "📡 Live Bus Tracking",
    live_subtitle: "Real-time bus location on map — auto-refreshes every 5 seconds",
    select_service: "Select Bus Service",
    type_service: "Or type service no.",
    track_btn: "📡 Track Bus",
    stop_btn: "Stop",
    tracking_active: "Tracking active",
    last_update: "Last update",
    bus_status: "Bus Status",
    eta: "ETA",
    route_stops: "Route Stops",
    select_to_track: "Select a bus to track",
    live_update_info: "Live location updates every 5 seconds",
    at_station: "At Station",
    approaching: "Approaching",
    en_route: "En Route",
    distance: "Distance",
    stops_left: "Stops left",
    speed: "Speed",
    updated: "Updated",
    nearest: "Nearest",

    // Admin
    admin_dashboard: "Admin Dashboard",
    management_dashboard: "Management Dashboard",
    overview: "Overview",
    routes: "Routes",
    services: "Services",
    vehicles: "Vehicles",
    stops: "Stops",
    drivers: "Drivers",
    bus_schedule: "Bus Schedule",
    admins: "Admins",
    quick_actions: "Quick Actions",
    system_info: "System Info",
    add_route: "Add Route",
    add_service: "Add Service",
    add_vehicle: "Add Vehicle",
    add_stop: "Add Stop",
    add_driver: "Add Driver",
    reseed_schedule: "Reseed Bus Schedule",
    delete: "Delete",
    cancel: "Cancel",

    // Driver Portal / Login
    driver_portal: "Driver Portal",
    driver_subtitle: "Login with your driver credentials",
    driver_username_label: "DRIVER USERNAME",
    driver_username_placeholder: "Enter driver username",
    password_label: "PASSWORD",
    password_placeholder: "Enter password",
    login_btn: "Login",
    or_divider: "OR",
    passenger_login: "Passenger Login",
    driver_note: "Driver accounts are created by admins only. Contact your supervisor if you cannot log in.",
    driver_login_sub: "Login with your driver credentials",
    driver_dashboard: "Driver Dashboard",
    assigned_service: "Assigned Service",
    assigned_route: "Assigned Route",
    location_broadcast: "Location Broadcast",
    broadcast_prompt: "Press the button below to start sharing your location",
    speed_kmh: "Speed (km/h)",
    service_override: "Service Override",
    start_broadcast: "📡 Start Broadcasting Location",
    broadcast_log: "Broadcast Log",
    clear: "Clear",
    stop_btn: "Stop",
    offline: "Offline",
    live_broadcasting: "Live Broadcasting",
    location_sent: "Location sent",
    location_updated: "Location updated successfully",
    not_assigned: "No route assigned yet",
    driver_info_box: "Driver accounts are created by admins only. Contact your supervisor if you cannot log in.",
    update_location: "Update My Location",
    captcha_error: "Please complete the CAPTCHA verification"
  },
  te: {
    // Shared / Header
    app_title: "APSRTC లైవ్",
    app_subtitle: "విశాఖపట్నం బస్ ట్రాకర్",
    navigation: "నావిగేషన్",
    search_buses: "బస్సులు వెతకండి",
    live_tracking: "లైవ్ ట్రాకింగ్",
    full_schedule: "పూర్తి షెడ్యూల్",
    admin_panel: "అడ్మిన్ పానెల్",
    driver_portal: "డ్రైవర్ పోర్టల్",
    logout: "లాగ్అవుట్",
    login: "లాగిన్",
    welcome_back: "తిరిగి స్వాగతం",
    login_sub: "మీ బస్సును లైవ్‌లో ట్రాక్ చేయడానికి లాగిన్ అవ్వండి",
    username: "వినియోగదారు పేరు",
    password: "పాస్వర్డ్",
    remember_me: "30 రోజుల పాటు గుర్తుంచుకో",
    new_user: "కొత్త వినియోగదారా? ఖాతాను సృష్టించండి",
    choose_username: "వినియోగదారు పేరు ఎంచుకోండి",
    choose_password: "పాస్వర్డ్ సృష్టించండి",
    create_account: "ఖాతాను సృష్టించండి",
    have_account: "ఇప్పటికే ఖాతా ఉందా? లాగిన్",

    // Search Section
    search_title: "మీ బస్సును కనుగొనండి",
    search_subtitle: "విశాఖపట్నం APSRTC — RTC కాంప్లెక్స్ నుండి నిజ-సమయ షెడ్యూల్‌లు",
    from: "నుండి",
    to: "వరకు",
    departure: "బయలుదేరే సమయం",
    arrival: "చేరే సమయం",
    duration: "వ్యవధి",
    bus_type: "బస్సు రకం",
    search_btn: "వెతకండి",
    all_destinations: "అన్ని గమ్యస్థానాలు",
    all_types: "అన్ని రకాలు",
    results_title: "శోధన ఫలితాలు",
    no_results: "బస్సులు కనుగొనబడలేదు",
    no_results_sub: "వేరే గమ్యస్థానం లేదా బస్సు రకాన్ని ప్రయత్నించండి",
    select_dest_prompt: "బస్సులను చూడటానికి ఒక గమ్యస్థానాన్ని ఎంచుకోండి",
    fare: "ధర",
    departs: "బయలుదేరుతుంది",
    arrives: "చేరుకుంటుంది",
    next_bus_in: "తదుపరి బస్సు",
    running: "నడుస్తోంది",
    found: "కనుగొనబడింది",
    buses: "బస్సులు",
    bus: "బస్సు",
    next_in: "తదుపరి బస్సు",
    departing_now: "ఇప్పుడే బయలుదేరుతోంది!",
    departing_soon: "త్వరలో బయలుదేరుతోంది!",
    min: "నిముషాల్లో",
    search_placeholder: "గమ్యం లేదా మార్గం వెతకండి...",

    // Schedule Table
    col_route: "మార్గం",
    col_destination: "గమ్యం",
    col_type: "రకం",
    col_departs: "బయలుదేరు",
    col_arrives: "చేరుకొనే",
    col_duration: "వ్యవధి",
    col_fare: "చార్జీ",
    col_next_bus: "తదుపరి బస్సు",
    full_schedule_heading: "పూర్తి షెడ్యూల్",

    // Bus Types
    metro_express: "మెట్రో ఎక్స్ప్రెస్",
    express: "ఎక్స్ప్రెస్",
    ordinary: "సాధారణ",

    // Live Tracking
    live_title: "📡 లైవ్ బస్ ట్రాకింగ్",
    live_subtitle: "మ్యాప్‌లో నిజ-సమయ బస్సు లొకేషన్ — ప్రతి 5 సెకన్లకు ఆటో-రిఫ్రెష్ అవుతుంది",
    select_service: "బస్సు సర్వీస్‌ను ఎంచుకోండి",
    type_service: "లేదా సర్వీస్ నంబర్ టైప్ చేయండి",
    track_btn: "📡 బస్సును ట్రాక్ చేయండి",
    stop_btn: "ఆపండి",
    tracking_active: "ట్రాకింగ్ యాక్టివ్‌గా ఉంది",
    last_update: "చివరి అప్‌డేట్",
    bus_status: "బస్సు స్థితి",
    eta: "చేరే సమయం",
    route_stops: "మార్గం స్టాప్‌లు",
    select_to_track: "ట్రాక్ చేయడానికి ఒక బస్సును ఎంచుకోండి",
    live_update_info: "ప్రతి 5 సెకన్లకు లైవ్ లొకేషన్ అప్‌డేట్ అవుతుంది",
    at_station: "స్టేషన్‌లో ఉంది",
    approaching: "వస్తోంది",
    en_route: "మార్గంలో ఉంది",
    distance: "దూరం",
    stops_left: "మిగిలి ఉన్న స్టాప్‌లు",
    speed: "వేగం",
    updated: "అప్‌డేట్ అయింది",
    nearest: "సమీప స్టాప్",

    // Admin
    admin_dashboard: "అడ్మిన్ డాష్‌బోర్డ్",
    management_dashboard: "మేనేజ్‌మెంట్ డాష్‌బోర్డ్",
    overview: "అవలోకనం",
    routes: "మార్గాలు",
    services: "సేవలు",
    vehicles: "వాహనాలు",
    stops: "స్టాప్‌లు",
    drivers: "డ్రైవర్లు",
    bus_schedule: "బస్సు షెడ్యూల్",
    admins: "అడ్మిన్లు",
    quick_actions: "త్వరిత చర్యలు",
    system_info: "సిస్టమ్ సమాచారం",
    add_route: "మార్గం జోడించండి",
    add_service: "సర్వీస్ జోడించండి",
    add_vehicle: "వాహనం జోడించండి",
    add_stop: "స్టాప్ జోడించండి",
    add_driver: "డ్రైవర్‌ను జోడించండి",
    reseed_schedule: "షెడ్యూల్ రీసీడ్ చేయండి",
    delete: "తొలగించు",
    cancel: "రద్దు",

    // Driver Portal / Login
    driver_portal: "డ్రైవర్ పోర్టల్",
    driver_subtitle: "మీ డ్రైవర్ వివరాలతో లాగిన్ చేయండి",
    driver_username_label: "డ్రైవర్ పేరు",
    driver_username_placeholder: "డ్రైవర్ పేరు నమోదు చేయండి",
    password_label: "పాస్వర్డ్",
    password_placeholder: "పాస్వర్డ్ నమోదు చేయండి",
    login_btn: "లాగిన్",
    or_divider: "లేదా",
    passenger_login: "ప్రయాణికుల లాగిన్",
    driver_note: "డ్రైవర్ ఖాతాలు అడ్మిన్లు మాత్రమే సృష్టిస్తారు. లాగిన్ కాలేకపోతే మీ సూపర్వైజర్ని సంప్రదించండి.",
    driver_login_sub: "మీ డ్రైవర్ వివరాలతో లాగిన్ అవ్వండి",
    driver_dashboard: "డ్రైవర్ డాష్‌బోర్డ్",
    assigned_service: "కేటాయించిన సర్వీస్",
    assigned_route: "కేటాయించిన మార్గం",
    location_broadcast: "లొకేషన్ బ్రాడ్‌కాస్ట్",
    broadcast_prompt: "మీ లొకేషన్‌ను షేర్ చేయడం ప్రారంభించడానికి క్రింది బటన్‌ను నొక్కండి",
    speed_kmh: "వేగం (కిమీ/గం)",
    service_override: "సర్వీస్ ఓవర్‌రైడ్",
    start_broadcast: "📡 లొకేషన్ బ్రాడ్‌కాస్ట్ ప్రారంభించండి",
    broadcast_log: "బ్రాడ్‌కాస్ట్ లాగ్",
    clear: "క్లియర్",
    stop_btn: "ఆపండి",
    offline: "ఆఫ్‌లైన్",
    live_broadcasting: "లైవ్ బ్రాడ్‌కాస్టింగ్",
    location_sent: "లొకేషన్ పంపబడింది",
    location_updated: "లొకేషన్ విజయవంతంగా అప్‌డేట్ అయింది",
    not_assigned: "మార్గం కేటాయించబడలేదు",
    driver_info_box: "డ్రైవర్ ఖాతాలు అడ్మిన్ల ద్వారా మాత్రమే సృష్టించబడతాయి. మీరు లాగిన్ చేయలేకపోతే మీ సూపర్‌వైజర్‌ను సంప్రదించండి.",
    update_location: "లొకేషన్ అప్‌డేట్ చేయండి",
    captcha_error: "దయచేసి CAPTCHA పూర్తి చేయండి"
  },
  hi: {
    // Shared / Header
    app_title: "APSRTC लाइव",
    app_subtitle: "विशाखापत्तनम बस ट्रैकर",
    navigation: "नेविगेशन",
    search_buses: "बसें खोजें",
    live_tracking: "लाइव ट्रैकिंग",
    full_schedule: "पूरा शेड्यूल",
    admin_panel: "एडमिन पैनल",
    driver_portal: "ड्राइवर पोर्टल",
    logout: "लॉगआउट",
    login: "लॉगिन",
    welcome_back: "वापस स्वागत है",
    login_sub: "अपनी बस को लाइव ट्रैक करने के लिए लॉगिन करें",
    username: "उपयोगकर्ता नाम",
    password: "पासवर्ड",
    remember_me: "30 दिनों के लिए याद रखें",
    new_user: "नए उपयोगकर्ता? खाता बनाएं",
    choose_username: "उपयोगकर्ता नाम चुनें",
    choose_password: "पासवर्ड बनाएं",
    create_account: "खाता बनाएं",
    have_account: "पहले से खाता है? लॉगिन",

    // Search Section
    search_title: "अपनी बस खोजें",
    search_subtitle: "विशाखापत्तनम APSRTC — RTC कॉम्प्लेक्स से रीयल-टाइम शेड्यूल",
    from: "से",
    to: "तक",
    departure: "प्रस्थान",
    arrival: "आगमन",
    duration: "अवधि",
    bus_type: "बस प्रकार",
    search_btn: "खोजें",
    all_destinations: "सभी गंतव्य",
    all_types: "सभी प्रकार",
    results_title: "खोज परिणाम",
    no_results: "कोई बस नहीं मिली",
    no_results_sub: "एक अलग गंतव्य या बस प्रकार का प्रयास करें",
    select_dest_prompt: "बसों को देखने के लिए एक गंतव्य चुनें",
    fare: "किराया",
    departs: "प्रस्थान",
    arrives: "आगमन",
    next_bus_in: "अगली बस",
    running: "चल रही है",
    found: "पाया",
    buses: "बसें",
    bus: "बस",
    next_in: "अगली",
    departing_now: "अभी प्रस्थान हो रही है!",
    departing_soon: "जल्द ही प्रस्थान होगी!",
    min: "मिनट में",
    search_placeholder: "गंतव्य या मार्ग खोजें...",

    // Schedule Table
    col_route: "मार्ग",
    col_destination: "गंतव्य",
    col_type: "प्रकार",
    col_departs: "प्रस्थान",
    col_arrives: "आगमन",
    col_duration: "अवधि",
    col_fare: "किराया",
    col_next_bus: "अगली बस",
    full_schedule_heading: "पूरा शेड्यूल",

    // Bus Types
    metro_express: "मेट्रो एक्सप्रेस",
    express: "एक्सप्रेस",
    ordinary: "साधारण",

    // Live Tracking
    live_title: "📡 लाइव बस ट्रैकिंग",
    live_subtitle: "मानचित्र पर रीयल-टाइम बस स्थान — हर 5 सेकंड में ऑटो-रिफ्रेश",
    select_service: "बसों की सेवा चुनें",
    type_service: "या सेवा संख्या टाइप करें",
    track_btn: "📡 बस ट्रैक करें",
    stop_btn: "रुकें",
    tracking_active: "ट्रैकिंग सक्रिय है",
    last_update: "पिछला अपडेट",
    bus_status: "बस की स्थिति",
    eta: "पहुंचने का समय",
    route_stops: "मार्ग के स्टॉप",
    select_to_track: "ट्रैक करने के लिए बस चुनें",
    live_update_info: "स्थान अपडेट हर 5 सेकंड में",
    at_station: "स्टेशन पर है",
    approaching: "आ रही है",
    en_route: "रास्ते में है",
    distance: "दूरी",
    stops_left: "स्टॉप बचे हैं",
    speed: "गति",
    updated: "अपडेट किया गया",
    nearest: "निकटतम स्टॉप",

    // Admin
    admin_dashboard: "एडमिन डैशबोर्ड",
    management_dashboard: "प्रबंधन डैशबोर्ड",
    overview: "अवलोकन",
    routes: "मार्ग",
    services: "सेवाएं",
    vehicles: "वाहन",
    stops: "स्टॉप",
    drivers: "ड्राइवर",
    bus_schedule: "बस शेड्यूल",
    admins: "एडमिन",
    quick_actions: "त्वरित कार्रवाई",
    system_info: "सिस्टम जानकारी",
    add_route: "मार्ग जोड़ें",
    add_service: "सेवा जोड़ें",
    add_vehicle: "वाहन जोड़ें",
    add_stop: "स्टॉप जोड़ें",
    add_driver: "ड्राइवर जोड़ें",
    reseed_schedule: "शेड्यूल रीसीड करें",
    delete: "हटाएं",
    cancel: "रद्द करें",

    // Driver Portal / Login
    driver_portal: "ड्राइवर पोर्टल",
    driver_subtitle: "अपने ड्राइवर क्रेडेंशियल से लॉगिन करें",
    driver_username_label: "ड्राइवर उपयोगकर्ता नाम",
    driver_username_placeholder: "ड्राइवर उपयोगकर्ता नाम दर्ज करें",
    password_label: "पासवर्ड",
    password_placeholder: "पासवर्ड दर्ज करें",
    login_btn: "लॉगिन",
    or_divider: "या",
    passenger_login: "यात्री लॉगिन",
    driver_note: "ड्राइवर खाते केवल एडमिन द्वारा बनाए जाते हैं। यदि लॉगिन नहीं कर पा रहे तो अपने सुपरवाइजर से संपर्क करें।",
    driver_login_sub: "अपने ड्राइवर क्रेडेंशियल्स के साथ लॉगिन करें",
    driver_dashboard: "ड्राइवर डैशबोर्ड",
    assigned_service: "सौंपा गया सेवा",
    assigned_route: "सौंपा गया मार्ग",
    location_broadcast: "स्थान प्रसारण",
    broadcast_prompt: "अपना स्थान साझा करना शुरू करने के लिए नीचे दिए गए बटन पर क्लिक करें",
    speed_kmh: "गति (किमी/घंटा)",
    service_override: "सेवा ओवरराइड",
    start_broadcast: "📡 स्थान प्रसारण शुरू करें",
    broadcast_log: "प्रसारण लॉग",
    clear: "साफ करें",
    stop_btn: "रुकें",
    offline: "ऑफ़लाइन",
    live_broadcasting: "लाइव प्रसारण",
    location_sent: "स्थान भेजा गया",
    location_updated: "स्थान सफलतापूर्वक अपडेट हुआ",
    not_assigned: "कोई मार्ग नहीं सौंपा गया",
    driver_info_box: "ड्राइवर खाते केवल एडमिन द्वारा बनाए जाते हैं। यदि आप लॉगिन नहीं कर पा रहे हैं तो अपने पर्यवेक्षक से संपर्क करें।",
    update_location: "स्थान अपडेट करें",
    captcha_error: "कृपया CAPTCHA सत्यापन पूरा करें"
  }
};

let currentLang = localStorage.getItem('lang') || 'en';

function applyLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('lang', lang);
  
  // Text content
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (translations[lang] && translations[lang][key]) {
      el.textContent = translations[lang][key];
    }
  });

  // Placeholders
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (translations[lang] && translations[lang][key]) {
      el.placeholder = translations[lang][key];
    }
  });

  // Dropdown options
  document.querySelectorAll('[data-i18n-option]').forEach(el => {
    const key = el.getAttribute('data-i18n-option');
    if (translations[lang] && translations[lang][key]) {
      el.textContent = translations[lang][key];
    }
  });

  // Highlight active language button
  document.querySelectorAll('.lang-btn').forEach(btn => {
    const btnLang = btn.getAttribute('data-lang');
    btn.classList.toggle('active', btnLang === lang);
  });
  
  // Set HTML lang attribute
  document.documentElement.lang = lang;

  // Trigger re-render of dynamic elements if functions exist
  if (typeof renderResults === 'function' && typeof allResults !== 'undefined') {
    renderResults(allResults);
  }
  if (typeof renderScheduleTable === 'function' && typeof schedData !== 'undefined') {
    renderScheduleTable(schedData);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const saved = localStorage.getItem('lang') || 'en';
  applyLanguage(saved);
});
