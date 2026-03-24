export default function SectionHeader({ eyebrow, title, description, actions }) {
  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        {eyebrow ? <p className="soc-kicker">{eyebrow}</p> : null}
        <h2 className="mt-2 font-headline text-[28px] font-extrabold tracking-tight text-white">{title}</h2>
        {description ? <p className="mt-2 max-w-3xl text-sm leading-6 soc-text-muted">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}
