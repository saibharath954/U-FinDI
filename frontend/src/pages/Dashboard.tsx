import { motion } from "framer-motion";
import {
  TrendingUp,
  FileCheck,
  AlertTriangle,
  BarChart3,
  Activity,
  Target,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const metrics = [
  { label: "Documents Processed", value: "12,847", change: "+18%", icon: FileCheck, up: true },
  { label: "Extraction Accuracy", value: "99.2%", change: "+2.1%", icon: Target, up: true },
  { label: "Validation Failures", value: "127", change: "-34%", icon: AlertTriangle, up: false },
  { label: "Avg Processing Time", value: "2.3s", change: "-0.8s", icon: Activity, up: false },
];

const accuracyOverTime = [
  { month: "Aug", accuracy: 91.2 },
  { month: "Sep", accuracy: 93.1 },
  { month: "Oct", accuracy: 94.8 },
  { month: "Nov", accuracy: 96.4 },
  { month: "Dec", accuracy: 97.9 },
  { month: "Jan", accuracy: 99.2 },
];

const errorDistribution = [
  { type: "Table Reconstruction", count: 42, pct: 33 },
  { type: "Entity Resolution", count: 31, pct: 24 },
  { type: "Handwritten Fields", count: 27, pct: 21 },
  { type: "Multi-Language", count: 18, pct: 14 },
  { type: "Poor Scan Quality", count: 9, pct: 7 },
];

const docTypes = [
  { type: "Bank Statements", count: 5423, pct: 42 },
  { type: "Payslips", count: 3084, pct: 24 },
  { type: "Invoices", count: 2055, pct: 16 },
  { type: "Agreements", count: 1285, pct: 10 },
  { type: "Settlement Letters", count: 642, pct: 5 },
  { type: "Others", count: 358, pct: 3 },
];

const Dashboard = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <section className="pt-24 pb-16">
        <div className="container">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-8"
          >
            <h1 className="text-3xl font-bold mb-2">
              Extraction Quality <span className="gradient-text">Dashboard</span>
            </h1>
            <p className="text-muted-foreground">Real-time pipeline performance and learning loop metrics.</p>
          </motion.div>

          {/* KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {metrics.map((m, i) => (
              <motion.div
                key={m.label}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                className="glass-card p-5"
              >
                <div className="flex items-center justify-between mb-3">
                  <m.icon size={18} className="text-primary" />
                  <span className={`text-xs font-medium flex items-center gap-1 ${
                    (m.up && m.label !== "Validation Failures") || (!m.up && m.label === "Validation Failures") || (!m.up && m.label === "Avg Processing Time")
                      ? "text-success"
                      : "text-destructive"
                  }`}>
                    <TrendingUp size={12} className={!m.up ? "rotate-180" : ""} />
                    {m.change}
                  </span>
                </div>
                <div className="text-2xl font-bold mb-1">{m.value}</div>
                <div className="text-xs text-muted-foreground">{m.label}</div>
              </motion.div>
            ))}
          </div>

          <div className="grid lg:grid-cols-2 gap-6 mb-6">
            {/* Accuracy Over Time */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="glass-card p-6"
            >
              <div className="flex items-center gap-2 mb-6">
                <BarChart3 size={16} className="text-primary" />
                <h3 className="font-semibold text-sm">Accuracy Improvement (Learning Loop)</h3>
              </div>
              <div className="flex items-end gap-3 h-48">
                {accuracyOverTime.map((d) => (
                  <div key={d.month} className="flex-1 flex flex-col items-center gap-2">
                    <span className="text-xs font-mono text-primary">{d.accuracy}%</span>
                    <motion.div
                      initial={{ height: 0 }}
                      animate={{ height: `${(d.accuracy - 88) * 8}px` }}
                      transition={{ delay: 0.5, duration: 0.6 }}
                      className="w-full rounded-t-md bg-gradient-to-t from-primary/40 to-primary"
                    />
                    <span className="text-xs text-muted-foreground">{d.month}</span>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Error Distribution */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="glass-card p-6"
            >
              <div className="flex items-center gap-2 mb-6">
                <AlertTriangle size={16} className="text-warning" />
                <h3 className="font-semibold text-sm">Error Distribution</h3>
              </div>
              <div className="space-y-4">
                {errorDistribution.map((e) => (
                  <div key={e.type}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted-foreground">{e.type}</span>
                      <span className="font-mono text-xs">{e.count} ({e.pct}%)</span>
                    </div>
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${e.pct}%` }}
                        transition={{ delay: 0.6, duration: 0.5 }}
                        className="h-full bg-warning/70 rounded-full"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Document Type Breakdown */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="glass-card p-6"
          >
            <div className="flex items-center gap-2 mb-6">
              <FileCheck size={16} className="text-primary" />
              <h3 className="font-semibold text-sm">Document Type Breakdown</h3>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {docTypes.map((d) => (
                <div key={d.type} className="text-center p-4 rounded-lg bg-secondary/50 border border-border/30">
                  <div className="text-xl font-bold gradient-text mb-1">{d.count.toLocaleString()}</div>
                  <div className="text-xs text-muted-foreground">{d.type}</div>
                  <div className="text-xs font-mono text-primary mt-1">{d.pct}%</div>
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

export default Dashboard;
