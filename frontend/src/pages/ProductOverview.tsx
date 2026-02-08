import { motion } from "framer-motion";
import {
  FileSearch,
  LayoutGrid,
  ImageIcon,
  Globe,
  Table2,
  UserCheck,
  CalendarCheck,
  DollarSign,
  GitBranch,
  RotateCcw,
  AlertTriangle,
  Cpu,
  ArrowDown,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.5, ease: "easeOut" as const },
  }),
};

const stages = [
  {
    title: "Document Intelligence",
    color: "primary",
    items: [
      { icon: FileSearch, label: "Auto-Classify", desc: "Identify document type from 200+ categories using vision + NLP models" },
      { icon: LayoutGrid, label: "Layout Detection", desc: "Detect tables, headers, stamps, handwritten sections, and signatures" },
      { icon: ImageIcon, label: "Quality Scoring", desc: "Assess scan quality, rotation, noise, and readability before extraction" },
      { icon: Globe, label: "Multi-Language", desc: "Support for English, Hindi, regional languages, and mixed-script documents" },
    ],
  },
  {
    title: "Extraction Engine",
    color: "primary",
    items: [
      { icon: Table2, label: "Schema-Aware Extraction", desc: "Map raw data to structured financial schemas with entity-aware parsing" },
      { icon: LayoutGrid, label: "Table Reconstruction", desc: "Rebuild complex multi-page tables with merged cells and spanning headers" },
      { icon: UserCheck, label: "Entity Resolution", desc: "Link same employer, bank, account across documents using fuzzy matching" },
    ],
  },
  {
    title: "Validation Layer",
    color: "primary",
    items: [
      { icon: DollarSign, label: "Balance Continuity", desc: "Verify opening/closing balances match across statement periods" },
      { icon: CalendarCheck, label: "Date Sequencing", desc: "Ensure chronological consistency and detect backdated entries" },
      { icon: AlertTriangle, label: "Income Plausibility", desc: "Flag anomalous salary patterns, round-tripping, and synthetic credits" },
      { icon: GitBranch, label: "Cross-Document Consistency", desc: "Match data across payslips, bank statements, and employment letters" },
    ],
  },
  {
    title: "Learning Loop",
    color: "primary",
    items: [
      { icon: UserCheck, label: "Human Correction Capture", desc: "Structured feedback from reviewers with field-level correction tracking" },
      { icon: RotateCcw, label: "Error Clustering", desc: "Group similar extraction errors to identify systematic model weaknesses" },
      { icon: Cpu, label: "Retraining Triggers", desc: "Automatic model updates when error clusters exceed confidence thresholds" },
    ],
  },
];

const ProductOverview = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <section className="pt-28 pb-16">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-w-3xl mx-auto text-center mb-16"
          >
            <h1 className="text-4xl font-bold mb-4">
              End-to-End <span className="gradient-text">Intelligence Pipeline</span>
            </h1>
            <p className="text-lg text-muted-foreground leading-relaxed">
              From raw document ingestion to validated financial knowledge—every stage is modular, 
              explainable, and continuously improving.
            </p>
          </motion.div>

          <div className="space-y-8">
            {stages.map((stage, si) => (
              <div key={stage.title}>
                <motion.div
                  initial="hidden"
                  whileInView="visible"
                  viewport={{ once: true }}
                  className="glass-card p-8"
                >
                  <motion.div variants={fadeUp} custom={0} className="flex items-center gap-3 mb-6">
                    <div className="h-8 w-8 rounded-lg bg-primary/20 flex items-center justify-center text-primary font-mono font-bold text-sm">
                      {si + 1}
                    </div>
                    <h2 className="text-xl font-bold">{stage.title}</h2>
                  </motion.div>

                  <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {stage.items.map((item, ii) => (
                      <motion.div
                        key={item.label}
                        variants={fadeUp}
                        custom={ii + 1}
                        className="p-4 rounded-lg bg-secondary/50 border border-border/50 hover:border-primary/20 transition-colors"
                      >
                        <item.icon className="text-primary mb-3" size={20} />
                        <h3 className="font-medium text-sm mb-1">{item.label}</h3>
                        <p className="text-xs text-muted-foreground leading-relaxed">{item.desc}</p>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>

                {si < stages.length - 1 && (
                  <div className="flex justify-center py-2">
                    <ArrowDown className="text-primary/30" size={24} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default ProductOverview;
