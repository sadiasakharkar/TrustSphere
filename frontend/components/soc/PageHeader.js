export default function PageHeader({ kicker, title, description, actions }) {
  return (
    <section className="mb-6 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
      <div>
        <p className="soc-kicker">{kicker}</p>
        <h1 className="soc-title mt-2">{title}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 soc-text-muted">{description}</p>
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
    </section>
  );
}
