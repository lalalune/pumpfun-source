import Link from 'next/link';
import type { ReactNode } from 'react';
import { BLOG_URL, LEGAL_LINKS, RESOURCE_LINKS, SOCIAL_LINKS, type MenuEntry } from '@/config/navigation';
import { FooterMenu } from './FooterMenu';
import { FooterOutboundLinks } from '@/components/links/footer-outbound-links';

const LINK_CLASS = 'text-text-tertiary transition-colors hover:text-text-primary';

/** The captured site footer: stacked link lists on mobile, a single row with menus from `md`. */
export function SiteFooter() {
  return <FooterOutboundLinks><SiteFooterContent /></FooterOutboundLinks>;
}

function SiteFooterContent() {
  const year = new Date().getFullYear();
  return (
    <footer className="z-[1] mt-auto border-t border-border-secondary bg-bg-primary text-text-tertiary max-md:mb-12">
      <div className="flex flex-col gap-8 px-[var(--padding-x-main)] pt-8 pb-4 md:hidden">
        <LinkList title="Resources" links={RESOURCE_LINKS} />
        <LinkList title="Legal" links={LEGAL_LINKS} />
        <div className="flex flex-col gap-2 text-sm">
          <ExternalLink href={BLOG_URL}>Blog</ExternalLink>
        </div>
        <div className="flex flex-col items-start gap-4 border-t border-border-secondary pt-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs">© Pump.fun {year}</p>
          <SocialLinks />
        </div>
      </div>
      <div className="mx-auto hidden w-full max-w-screen-2xl flex-wrap items-center justify-between gap-x-6 gap-y-2 px-[var(--padding-x-main)] pt-[var(--site-footer-pad-top,1.5rem)] pb-[var(--site-footer-pad-bottom,0.5rem)] text-xs md:flex">
        <p className="whitespace-nowrap">© Pump.fun {year}</p>
        <nav aria-label="Footer" className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <ExternalLink href={BLOG_URL}>Blog</ExternalLink>
          <FooterMenu title="Resources" links={RESOURCE_LINKS} />
          <FooterMenu title="Legal" links={LEGAL_LINKS} />
        </nav>
        <SocialLinks />
      </div>
    </footer>
  );
}

function LinkList({ title, links }: { title: string; links: readonly MenuEntry[] }) {
  return (
    <nav aria-label={title}>
      <h2 className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-secondary">{title}</h2>
      <ul className="flex flex-col gap-2 text-sm">
        {links.map((link) => (
          <li key={link.label}>
            {link.external ? (
              <ExternalLink href={link.href!}>{link.label}</ExternalLink>
            ) : (
              <Link className={LINK_CLASS} href={link.href!}>
                {link.label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </nav>
  );
}

function ExternalLink({ href, children, label }: { href: string; children?: ReactNode; label?: string }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" aria-label={label} className={LINK_CLASS}>
      {children}
    </a>
  );
}

function SocialLinks() {
  return (
    <div className="flex items-center gap-4">
      {SOCIAL_LINKS.map(({ label, href, icon: SocialIcon }) => (
        <ExternalLink key={label} href={href} label={label}>
          <SocialIcon />
        </ExternalLink>
      ))}
    </div>
  );
}
