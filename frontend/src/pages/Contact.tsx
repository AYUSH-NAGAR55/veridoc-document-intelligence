import { useState } from "react";
import { PublicNav } from "../components/PublicNav";

export default function Contact() {
  const [submitted, setSubmitted] = useState(false);

  return (
    <div>
      <PublicNav />
      <section className="container-page py-16 max-w-lg">
        <h1 className="text-3xl font-semibold text-ink">Contact</h1>
        <p className="text-inkmuted mt-3">
          Questions, feedback, or a demo request — this form is a template ready to wire up to your
          own email or CRM provider.
        </p>

        {submitted ? (
          <div className="mt-8 bg-mint-pastel text-mint-deep rounded-xl2 p-6">
            <p className="font-medium">Thanks — your message has been noted.</p>
            <p className="text-sm mt-1">This is a demo form; connect it to a mail or CRM endpoint to receive real submissions.</p>
          </div>
        ) : (
          <form
            className="mt-8 space-y-4"
            onSubmit={(e) => {
              e.preventDefault();
              setSubmitted(true);
            }}
          >
            <div>
              <label htmlFor="name" className="text-sm font-medium text-ink">Name</label>
              <input id="name" required className="mt-1 w-full border border-line rounded-lg px-3.5 py-2.5 bg-surface focus:border-blue-deep outline-none" />
            </div>
            <div>
              <label htmlFor="email" className="text-sm font-medium text-ink">Email</label>
              <input id="email" type="email" required className="mt-1 w-full border border-line rounded-lg px-3.5 py-2.5 bg-surface focus:border-blue-deep outline-none" />
            </div>
            <div>
              <label htmlFor="message" className="text-sm font-medium text-ink">Message</label>
              <textarea id="message" required rows={4} className="mt-1 w-full border border-line rounded-lg px-3.5 py-2.5 bg-surface focus:border-blue-deep outline-none" />
            </div>
            <button type="submit" className="bg-blue-deep text-white font-medium px-5 py-2.5 rounded-lg hover:bg-blue-deep/90 transition-colors">
              Send message
            </button>
          </form>
        )}
      </section>
    </div>
  );
}
