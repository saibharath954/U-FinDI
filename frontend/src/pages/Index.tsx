import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  FileText,
  Brain,
  ShieldCheck,
  BarChart3,
  Zap,
  ArrowRight,
  Layers,
  RefreshCw,
  CheckCircle2,
  TrendingUp,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: "easeOut" as const },
  }),
};

const stats = [
  { value: "200+", label: "Document Types" },
  { value: "99.2%", label: "Extraction Accuracy" },
  { value: "<3s", label: "Processing Time" },
  { value: "40%", label: "Cost Reduction" },
];

const features = [
  {
    icon: FileText,
    title: "Intelligent Classification",
    desc: "Auto-detect 200+ document types—bank statements, invoices, payslips, settlement letters—regardless of layout or quality.",
  },
  {
    icon: Brain,
    title: "Self-Learning AI",
    desc: "Every human correction improves the model. Error clustering and retraining triggers ensure the system gets smarter with each document.",
  },
  {
    icon: ShieldCheck,
    title: "Validation & Trust",
    desc: "Balance continuity, date sequencing, income plausibility, and cross-document consistency checks built into every extraction.",
  },
  {
    icon: BarChart3,
    title: "Explainable Confidence",
    desc: "Per-field confidence scores with audit trails. Know exactly why a value was extracted and how reliable it is.",
  },
  {
    icon: Layers,
    title: "Schema-Aware Extraction",
    desc: "Structured output mapped to your lending data model. Tables reconstructed, entities resolved, relationships preserved.",
  },
  {
    icon: RefreshCw,
    title: "Human-in-the-Loop",
    desc: "Reviewers correct edge cases in an intuitive UI. Corrections feed directly into the learning loop for continuous improvement.",
  },
];

const workflow = [
  { icon: FileText, label: "Upload", desc: "Drop any financial document" },
  { icon: Zap, label: "Classify", desc: "Auto-detect type & layout" },
  { icon: Brain, label: "Extract", desc: "Schema-aware data extraction" },
  { icon: CheckCircle2, label: "Validate", desc: "Cross-check & verify" },
  { icon: TrendingUp, label: "Learn", desc: "Improve with every correction" },
];

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      {/* Hero */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        <div className="absolute inset-0 grid-pattern opacity-30" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-primary/5 rounded-full blur-3xl" />
        
        <div className="container relative">
          <motion.div
            initial="hidden"
            animate="visible"
            className="max-w-4xl mx-auto text-center"
          >
            <motion.div variants={fadeUp} custom={0} className="mb-6">
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/30 bg-primary/10 text-primary text-xs font-medium">
                <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse-glow" />
                Hackathon Final Round — Live Demo
              </span>
            </motion.div>

            <motion.h1
              variants={fadeUp}
              custom={1}
              className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6"
            >
              From Unstructured Financial Documents to{" "}
              <span className="gradient-text">Verified Financial Intelligence</span>
            </motion.h1>

            <motion.p
              variants={fadeUp}
              custom={2}
              className="text-lg text-muted-foreground max-w-2xl mx-auto mb-8 leading-relaxed"
            >
              Rule-based OCR breaks on every new layout, poor scan, and inconsistent format. 
              U-FinDI is a self-learning AI system that ingests any financial document and converts it 
              into a validated knowledge object trusted for lending, underwriting, and compliance.
            </motion.p>

            <motion.div
              variants={fadeUp}
              custom={3}
              className="flex flex-col sm:flex-row gap-4 justify-center"
            >
              <Link
                to="/upload"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-all glow-sm hover:glow"
              >
                Upload Document
                <ArrowRight size={18} />
              </Link>
              <Link
                to="/dashboard"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg border border-border bg-secondary text-secondary-foreground font-medium hover:bg-secondary/80 transition-colors"
              >
                View Demo Dashboard
              </Link>
            </motion.div>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            {stats.map((s) => (
              <div key={s.label} className="glass-card p-6 text-center">
                <div className="text-3xl font-bold gradient-text mb-1">{s.value}</div>
                <div className="text-sm text-muted-foreground">{s.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Workflow */}
      <section className="py-20 border-t border-border/50">
        <div className="container">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl font-bold mb-3">How It Works</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Five-stage intelligent pipeline from raw document to verified financial data.
            </p>
          </motion.div>

          <div className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-0">
            {workflow.map((step, i) => (
              <motion.div
                key={step.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="flex items-center gap-4"
              >
                <div className="flex flex-col items-center text-center w-36">
                  <div className="h-14 w-14 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center mb-3">
                    <step.icon className="text-primary" size={24} />
                  </div>
                  <span className="font-semibold text-sm">{step.label}</span>
                  <span className="text-xs text-muted-foreground mt-1">{step.desc}</span>
                </div>
                {i < workflow.length - 1 && (
                  <ArrowRight className="hidden md:block text-muted-foreground/30 shrink-0" size={20} />
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 border-t border-border/50">
        <div className="container">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl font-bold mb-3">Why U-FinDI</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Purpose-built for fintech operations teams who need accuracy, speed, and trust at scale.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="glass-card p-6 hover:border-primary/30 transition-colors group"
              >
                <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                  <f.icon className="text-primary" size={20} />
                </div>
                <h3 className="font-semibold mb-2">{f.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 border-t border-border/50">
        <div className="container">
          <div className="glass-card p-12 text-center glow relative overflow-hidden">
            <div className="absolute inset-0 dot-pattern opacity-20" />
            <div className="relative">
              <h2 className="text-3xl font-bold mb-4">See U-FinDI in Action</h2>
              <p className="text-muted-foreground max-w-lg mx-auto mb-8">
                Upload a financial document and watch the AI classify, extract, and validate in real-time.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link
                  to="/upload"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-all"
                >
                  Try the Upload Flow
                  <ArrowRight size={18} />
                </Link>
                <Link
                  to="/reviewer"
                  className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg border border-border bg-secondary text-secondary-foreground font-medium hover:bg-secondary/80 transition-colors"
                >
                  Explore Reviewer UI
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Index;
