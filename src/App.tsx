import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { AnalyzeSection } from './components/AnalyzeSection';
import { CorridorPlanner } from './components/CorridorPlanner';
import { Footer } from './components/Footer';

export default function App() {
  return (
    <>
      {/* Delicate cartographic graticule background */}
      <div className="bg-mesh" aria-hidden="true" />
      <div className="bg-grain" aria-hidden="true" />

      {/* Accessible skip link for keyboard users */}
      <a
        href="#analyze"
        className="sr-only"
        style={{
          position: 'absolute',
          top: 8,
          left: 8,
          zIndex: 9999,
          padding: '8px 16px',
          background: 'var(--signal-teal)',
          color: 'var(--obsidian-ink)',
          borderRadius: 'var(--radius-xs)',
          fontFamily: 'var(--font-mono)',
          fontWeight: 700,
          textDecoration: 'none',
        }}
        onFocus={e => {
          (e.currentTarget as HTMLElement).style.clip = 'auto';
          (e.currentTarget as HTMLElement).style.width = 'auto';
          (e.currentTarget as HTMLElement).style.height = 'auto';
        }}
        onBlur={e => {
          (e.currentTarget as HTMLElement).style.clip = 'rect(0,0,0,0)';
          (e.currentTarget as HTMLElement).style.width = '1px';
          (e.currentTarget as HTMLElement).style.height = '1px';
        }}
      >
        Skip to analysis workbench
      </a>

      <Navbar />

      <main id="main-content" style={{ position: 'relative', zIndex: 2 }}>
        <Hero />

        {/* Hairline datum divider */}
        <div
          style={{
            height: 1,
            background: 'linear-gradient(90deg, transparent, var(--border-fine), transparent)',
            margin: '0 2rem',
          }}
          aria-hidden="true"
        />

        <AnalyzeSection />

        <div
          style={{
            height: 1,
            background: 'linear-gradient(90deg, transparent, var(--border-fine), transparent)',
            margin: '0 2rem',
          }}
          aria-hidden="true"
        />

        {/* Multimodal Transit Corridors (Mode A Curated & Mode B Custom Routing) */}
        <CorridorPlanner />
      </main>

      <Footer />
    </>
  );
}
