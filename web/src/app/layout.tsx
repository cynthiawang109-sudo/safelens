import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
export const metadata: Metadata = {
  title: "SafeLens · Evidence, in context",
  description: "Explore ASRS reporter accounts with traceable evidence.",
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <a className="skip-link" href="#main">
          Skip to content
        </a>
        <header className="site-header">
          <div className="header-inner">
            <Link href="/" className="brand" aria-label="SafeLens home">
              <span className="brand-mark" aria-hidden="true">
                ↗
              </span>
              <span>
                SafeLens
                <span className="brand-caption">ASRS RESEARCH WORKSPACE</span>
              </span>
            </Link>
            <nav aria-label="Main navigation">
              <Link href="/">Ask & explore</Link>
              <Link href="/results">Evaluation lab ↗</Link>
            </nav>
            <span className="research-label">
              <span className="tiny-dot" />
              Research use
            </span>
          </div>
        </header>
        <main id="main" className="main-shell">
          {children}
        </main>
        <footer className="site-footer">
          <span>Voluntary reporter accounts. Not confirmed findings.</span>
          <span>Evidence first. Uncertainty visible.</span>
        </footer>
      </body>
    </html>
  );
}
