import { motion } from "framer-motion";
import {
  FileInput,
  Brain,
  ShieldCheck,
  RotateCcw,
  Database,
  Server,
  Users,
  ArrowRight,
  ArrowDown,
  Cpu,
  Eye,
  GitBranch,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const layers = [
  {
    title: "Ingestion Layer",
    icon: FileInput,
    desc: "Multi-format document intake with quality assessment",
    modules: ["PDF/Image Parser", "Quality Scorer", "Format Normalizer", "OCR Engine"],
  },
  {
    title: "Intelligence Layer",
    icon: Brain,
    desc: "AI-powered classification, extraction, and entity resolution",
    modules: ["Document Classifier", "Layout Analyzer", "Schema Extractor", "Entity Resolver"],
  },
  {
    title: "Validation Layer",
    icon: ShieldCheck,
    desc: "Rule-based and ML-driven consistency verification",
    modules: ["Balance Checker", "Date Validator", "Plausibility Engine", "Cross-Doc Matcher"],
  },
  {
    title: "Learning Layer",
    icon: RotateCcw,
    desc: "Continuous improvement through human-in-the-loop feedback",
    modules: ["Correction Capture", "Error Clusterer", "Retrain Scheduler", "Model Registry"],
  },
];

const outputs = [
  { icon: Database, label: "Financial Knowledge Graph", desc: "Structured JSON objects with validated financial entities and relationships" },
  { icon: Eye, label: "Explainability Layer", desc: "Per-field confidence scores, validation traces, and correction history" },
  { icon: GitBranch, label: "API & Integrations", desc: "REST/GraphQL APIs for LOS, underwriting, and compliance systems" },
];

const Architecture = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <section className="pt-28 pb-16">
        <div className="container max-w-5xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-16"
          >
            <h1 className="text-4xl font-bold mb-4">
              System <span className="gradient-text">Architecture</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Modular microservice pipeline designed for scale, reliability, and continuous learning.
            </p>
          </motion.div>

          {/* Pipeline */}
          <div className="space-y-4 mb-16">
            {layers.map((layer, i) => (
              <div key={layer.title}>
                <motion.div
                  initial={{ opacity: 0, x: i % 2 === 0 ? -30 : 30 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="glass-card p-6"
                >
                  <div className="flex items-start gap-4">
                    <div className="h-12 w-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center shrink-0">
                      <layer.icon className="text-primary" size={24} />
                    </div>
                    <div className="flex-1">
                      <h3 className="font-bold text-lg mb-1">{layer.title}</h3>
                      <p className="text-sm text-muted-foreground mb-4">{layer.desc}</p>
                      <div className="flex flex-wrap gap-2">
                        {layer.modules.map((m) => (
                          <span
                            key={m}
                            className="px-3 py-1.5 rounded-md bg-secondary border border-border/50 text-xs font-medium text-secondary-foreground"
                          >
                            {m}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </motion.div>
                {i < layers.length - 1 && (
                  <div className="flex justify-center py-1">
                    <ArrowDown className="text-primary/30" size={20} />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Output */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <h2 className="text-2xl font-bold text-center mb-8">Output & Deliverables</h2>
            <div className="grid md:grid-cols-3 gap-6">
              {outputs.map((o, i) => (
                <motion.div
                  key={o.label}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="glass-card p-6 text-center"
                >
                  <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                    <o.icon className="text-primary" size={24} />
                  </div>
                  <h3 className="font-semibold mb-2">{o.label}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{o.desc}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* System Diagram */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="glass-card p-8 glow"
          >
            <h3 className="font-bold text-center mb-8">Microservice Flow</h3>
            <div className="flex flex-col md:flex-row items-center justify-center gap-4">
              {[
                { icon: Users, label: "Clients" },
                { icon: Server, label: "API Gateway" },
                { icon: Cpu, label: "Processing" },
                { icon: Brain, label: "AI Models" },
                { icon: Database, label: "Knowledge Store" },
              ].map((node, i, arr) => (
                <div key={node.label} className="flex items-center gap-4">
                  <div className="flex flex-col items-center">
                    <div className="h-14 w-14 rounded-xl bg-secondary border border-border flex items-center justify-center">
                      <node.icon className="text-primary" size={22} />
                    </div>
                    <span className="text-xs text-muted-foreground mt-2">{node.label}</span>
                  </div>
                  {i < arr.length - 1 && (
                    <ArrowRight className="hidden md:block text-primary/30 shrink-0" size={20} />
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Architecture;
