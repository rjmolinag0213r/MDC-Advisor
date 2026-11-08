/* ------------------------------------------------------------------
   SAMPLE DATA: NOT VERIFIED
   These records are placeholders for building and testing the search.
   Program names, credentials and career links must be checked against
   the official MDC catalog before anyone relies on them.
   Later this file is replaced by records from the PostgreSQL database.
   ------------------------------------------------------------------ */

window.MDC_SAMPLE_DATA = {
  // Interest chips shown on the Explore page.
  interests: [
    { id: "build",   label: "Build things" },
    { id: "solve",   label: "Solve puzzles" },
    { id: "create",  label: "Create with your hands" },
    { id: "help",    label: "Help people" },
    { id: "tech",    label: "Technology" },
    { id: "business",label: "Business and money" },
    { id: "arts",    label: "Art and media" },
    { id: "health",  label: "Health and science" }
  ],

  // Everyday words students type, mapped to words that appear in the records.
  synonyms: {
    computer: ["tech", "it", "software"], computers: ["tech", "it", "software"],
    coding: ["software", "programming"], code: ["software", "programming"],
    hacking: ["cybersecurity"], hacker: ["cybersecurity"], security: ["cybersecurity"],
    cooking: ["culinary", "chef"], cook: ["culinary", "chef"], food: ["culinary", "chef"],
    drawing: ["design", "art"], draw: ["design", "art"],
    buildings: ["architecture", "construction"], houses: ["architecture", "construction"],
    machines: ["engineering", "mechanical"], cars: ["engineering", "mechanical"],
    doctor: ["health", "medical"], hospital: ["nursing", "health"], nurse: ["nursing"],
    money: ["business", "finance", "accounting"], finance: ["accounting", "business"],
    movies: ["film", "video"], video: ["film"], camera: ["film"],
    kids: ["education", "teacher"], teaching: ["education", "teacher"],
    law: ["paralegal", "legal"], lawyer: ["paralegal", "legal"],
    animals: ["biology", "science"]
  },

  programs: [
    {
      id: "aa-engineering",
      name: "Associate in Arts, Engineering transfer track",
      credential: "A.A.",
      interests: ["build", "solve"],
      careers: ["Mechanical engineer", "Civil engineer", "Electrical engineer"],
      keywords: ["engineering", "mechanical", "math", "physics", "transfer"],
      summary: "Complete your first two years at MDC, then transfer to a university to finish an engineering bachelor's."
    },
    {
      id: "as-architecture",
      name: "Architectural Design and Construction Technology",
      credential: "A.S.",
      interests: ["build", "create", "arts"],
      careers: ["Architect", "Architectural drafter", "Construction manager"],
      keywords: ["architecture", "construction", "design", "buildings", "cad"],
      summary: "Learn drafting, design and building systems, with a path toward a university architecture degree."
    },
    {
      id: "bas-cybersecurity",
      name: "Cybersecurity",
      credential: "B.A.S.",
      interests: ["solve", "tech"],
      careers: ["Cybersecurity specialist", "Security analyst", "IT consultant"],
      keywords: ["cybersecurity", "security", "networks", "it"],
      summary: "Protect networks and data. Builds on an associate degree in a technology field."
    },
    {
      id: "as-it",
      name: "Information Technology",
      credential: "A.S.",
      interests: ["tech", "solve"],
      careers: ["IT support specialist", "Network technician", "IT consultant"],
      keywords: ["it", "tech", "networks", "help desk", "software"],
      summary: "Hands-on computer support, networking and systems skills for entry-level IT jobs."
    },
    {
      id: "as-software",
      name: "Computer Programming and Analysis",
      credential: "A.S.",
      interests: ["tech", "solve", "create"],
      careers: ["Software developer", "Web developer", "Applications analyst"],
      keywords: ["software", "programming", "coding", "apps", "web"],
      summary: "Write software and web applications, from programming basics to full projects."
    },
    {
      id: "as-culinary",
      name: "Culinary Arts Management",
      credential: "A.S.",
      interests: ["create", "business"],
      careers: ["Chef", "Kitchen manager", "Caterer"],
      keywords: ["culinary", "chef", "cooking", "food", "restaurant"],
      summary: "Professional cooking plus the management side of running a kitchen."
    },
    {
      id: "as-nursing",
      name: "Nursing",
      credential: "A.S.",
      interests: ["help", "health"],
      careers: ["Registered nurse"],
      keywords: ["nursing", "nurse", "health", "medical", "hospital"],
      summary: "Prepares you for the registered nurse licensing exam. Admission is competitive."
    },
    {
      id: "bsn-nursing",
      name: "Nursing (RN to BSN)",
      credential: "B.S.N.",
      interests: ["help", "health"],
      careers: ["Registered nurse", "Nurse manager"],
      keywords: ["nursing", "nurse", "bachelor", "health"],
      summary: "For licensed registered nurses who want to finish a bachelor's degree."
    },
    {
      id: "aa-business",
      name: "Associate in Arts, Business transfer track",
      credential: "A.A.",
      interests: ["business"],
      careers: ["Accountant", "Financial analyst", "Business owner"],
      keywords: ["business", "accounting", "finance", "money", "transfer"],
      summary: "General education plus business prerequisites, built to transfer into a business bachelor's."
    },
    {
      id: "as-film",
      name: "Film Production Technology",
      credential: "A.S.",
      interests: ["arts", "create", "tech"],
      careers: ["Film editor", "Camera operator", "Production assistant"],
      keywords: ["film", "video", "movies", "camera", "editing"],
      summary: "Hands-on film and video production, from camera work to editing."
    },
    {
      id: "as-graphic",
      name: "Graphic and Interactive Design",
      credential: "A.S.",
      interests: ["arts", "create", "tech"],
      careers: ["Graphic designer", "UX designer", "Web designer"],
      keywords: ["design", "art", "drawing", "graphics", "web", "ux"],
      summary: "Visual design for print, web and apps."
    },
    {
      id: "as-paralegal",
      name: "Paralegal Studies",
      credential: "A.S.",
      interests: ["help", "business"],
      careers: ["Paralegal", "Legal assistant"],
      keywords: ["paralegal", "legal", "law", "lawyer"],
      summary: "Legal research, writing and office procedures for work alongside attorneys."
    },
    {
      id: "aa-education",
      name: "Associate in Arts, Education transfer track",
      credential: "A.A.",
      interests: ["help"],
      careers: ["Elementary teacher", "Teacher's aide"],
      keywords: ["education", "teacher", "teaching", "kids", "school"],
      summary: "Start toward a teaching career, with a path into an education bachelor's."
    },
    {
      id: "aa-biology",
      name: "Associate in Arts, Biology transfer track",
      credential: "A.A.",
      interests: ["health", "solve"],
      careers: ["Lab technician", "Pre-med student", "Environmental scientist"],
      keywords: ["biology", "science", "lab", "medical", "animals", "environment"],
      summary: "Science foundations for transfer into biology, pre-med or environmental programs."
    }
  ]
};
