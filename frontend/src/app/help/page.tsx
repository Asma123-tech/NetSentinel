export default function HelpPage() {
  const faqs = [
    {
      question: "What is NetSentinel?",
      answer: "NetSentinel is a safe search engine specially designed for kids to provide safer browsing with content filtering options."
    },
    {
      question: "How many filter modes does it provide?",
      answer: "It provides two filter modes:\n1. Relaxed mode – applies lighter filtering, allowing most content through.\n2. Strict mode – applies stronger filtering, blocking more sensitive or restricted content."
    },
    {
      question: "How does Strict mode work?",
      answer: "Strict mode filters potentially harmful or adult content and ensures safer search results."
    },
    {
      question: "Can I change filter settings?",
      answer: "Yes, you can change your filter mode anytime from the Settings page."
    },
    {
      question: "Can I save my search history?",
      answer: "Yes, you can save your search history and control it from the Settings page."
    },
    {
      question: "Is NetSentinel free to use?",
      answer: "Yes, NetSentinel is completely free for all users, providing safe browsing without any subscription."
    },
    {
      question: "Can NetSentinel be used without an internet connection?",
      answer: "No, NetSentinel requires an active internet connection to provide search results."
    }
  ];

  return (
    <div className="relative min-h-screen">
      {/* FULL BACKGROUND IMAGE */}
      <div className="fixed inset-0 -z-[5] bg-cover bg-center pointer-events-none blur-md scale-105"
        style={{ backgroundImage: "url('/images/1.jpg')" }}>
      </div>

      {/* OPTIONAL OVERLAY FOR BETTER READABILITY */}
      <div className="fixed inset-0 -z-[4] bg-white/50 pointer-events-none md:block hidden"></div>
      <div className="fixed inset-0 -z-[4] bg-white/30 pointer-events-none block md:hidden"></div>

      <div className="relative z-10 px-6 py-10 max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-slate-900 mb-8">
          Help & FAQs
        </h1>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <details
              key={index}
              className="bg-white/70 backdrop-blur-xl border border-slate-200 rounded-xl p-5 shadow-sm hover:shadow-md transition"
            >
              <summary className="cursor-pointer text-lg font-semibold text-slate-800">
                {faq.question}
              </summary>
              <p className="mt-3 text-slate-600 text-sm leading-relaxed">
                {faq.answer}
              </p>
            </details>
          ))}
        </div>
      </div>
    </div>
  );
}
