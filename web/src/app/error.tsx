"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <section className="card card-pad">
      <h1>This view could not load.</h1>
      <p className="lead">
        Your reports have not changed. Please try loading the view again.
      </p>
      <button className="primary-button" onClick={reset}>
        Try again
      </button>
    </section>
  );
}
