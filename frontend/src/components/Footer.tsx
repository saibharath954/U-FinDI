import { Link } from "react-router-dom";

const Footer = () => (
  <footer className="border-t border-border/50 bg-card/30">
    <div className="container py-12">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <span className="font-mono font-bold text-primary-foreground text-sm">UF</span>
            </div>
            <span className="font-semibold text-lg">U-FinDI</span>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Universal Financial Document Intelligence Engine. Turning unstructured documents into verified financial knowledge.
          </p>
        </div>
        <div>
          <h4 className="font-semibold mb-3 text-sm">Product</h4>
          <div className="flex flex-col gap-2">
            <Link to="/product" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Overview</Link>
            <Link to="/upload" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Upload</Link>
            <Link to="/reviewer" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Reviewer</Link>
          </div>
        </div>
        <div>
          <h4 className="font-semibold mb-3 text-sm">Platform</h4>
          <div className="flex flex-col gap-2">
            <Link to="/dashboard" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Dashboard</Link>
            <Link to="/architecture" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Architecture</Link>
          </div>
        </div>
        <div>
          <h4 className="font-semibold mb-3 text-sm">Built For</h4>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Digital lenders, underwriters, and compliance teams processing 200+ document types at scale.
          </p>
        </div>
      </div>
      <div className="mt-8 pt-8 border-t border-border/50 text-center">
        <p className="text-xs text-muted-foreground">© 2026 U-FinDI. Hackathon Demo — Universal Financial Document Intelligence Engine.</p>
      </div>
    </div>
  </footer>
);

export default Footer;
