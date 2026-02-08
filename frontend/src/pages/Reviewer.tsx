import { useState } from "react";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  AlertTriangle,
  Edit3,
  Save,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  FileText,
  Brain,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

interface Field {
  key: string;
  label: string;
  value: string;
  confidence: number;
  corrected?: string;
}

const initialFields: Field[] = [
  { key: "account_holder", label: "Account Holder", value: "Rajesh Kumar Sharma", confidence: 98.2 },
  { key: "bank_name", label: "Bank Name", value: "HDFC Bank Ltd.", confidence: 99.1 },
  { key: "account_number", label: "Account Number", value: "XXXX XXXX 4521", confidence: 96.7 },
  { key: "ifsc", label: "IFSC Code", value: "HDFC0001234", confidence: 97.8 },
  { key: "statement_period", label: "Statement Period", value: "01 Jan 2025 – 31 Jan 2025", confidence: 95.3 },
  { key: "opening_balance", label: "Opening Balance", value: "₹1,24,567.89", confidence: 93.4 },
  { key: "closing_balance", label: "Closing Balance", value: "₹1,87,234.56", confidence: 91.2 },
  { key: "total_credits", label: "Total Credits", value: "₹3,45,000.00", confidence: 88.7 },
  { key: "total_debits", label: "Total Debits", value: "₹2,82,333.33", confidence: 87.9 },
  { key: "salary_credit", label: "Salary Credit", value: "₹85,000.00", confidence: 72.4 },
  { key: "employer", label: "Employer Name", value: "Infosys Technologies Ltd", confidence: 68.3 },
];

const transactions = [
  { date: "02 Jan", desc: "NEFT-INFOSYS TECH", credit: "₹85,000", debit: "", balance: "₹2,09,567.89" },
  { date: "05 Jan", desc: "UPI/SWIGGY", credit: "", debit: "₹456.00", balance: "₹2,09,111.89" },
  { date: "10 Jan", desc: "EMI-HDFC HOME LOAN", credit: "", debit: "₹32,500.00", balance: "₹1,76,611.89" },
  { date: "15 Jan", desc: "UPI/AMAZON", credit: "", debit: "₹2,340.00", balance: "₹1,74,271.89" },
  { date: "20 Jan", desc: "NEFT-DIVIDEND", credit: "₹12,962.67", balance: "₹1,87,234.56", debit: "" },
];

const Reviewer = () => {
  const [fields, setFields] = useState(initialFields);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [saved, setSaved] = useState(false);
  const [showTransactions, setShowTransactions] = useState(true);

  const startEdit = (field: Field) => {
    setEditingKey(field.key);
    setEditValue(field.corrected || field.value);
  };

  const saveEdit = (key: string) => {
    setFields((prev) =>
      prev.map((f) =>
        f.key === key ? { ...f, corrected: editValue !== f.value ? editValue : undefined } : f
      )
    );
    setEditingKey(null);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  const confidenceColor = (c: number) =>
    c >= 90 ? "text-success" : c >= 75 ? "text-warning" : "text-destructive";

  const confidenceBg = (c: number) =>
    c >= 90 ? "bg-success/10" : c >= 75 ? "bg-warning/10" : "bg-destructive/10";

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <section className="pt-20 pb-8">
        <div className="container">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold">Document Review</h1>
              <p className="text-sm text-muted-foreground">HDFC_Statement_Jan2025.pdf — Bank Statement</p>
            </div>
            <div className="flex items-center gap-3">
              {saved && (
                <motion.span
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="text-sm text-success flex items-center gap-1"
                >
                  <Brain size={14} />
                  Learning applied for future documents
                </motion.span>
              )}
              <span className="px-3 py-1.5 rounded-md bg-success/10 text-success text-xs font-medium flex items-center gap-1">
                <CheckCircle2 size={12} /> High Confidence
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="pb-16">
        <div className="container">
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Left: Document Preview */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass-card overflow-hidden"
            >
              <div className="p-4 border-b border-border/50 flex items-center gap-2">
                <FileText size={16} className="text-primary" />
                <span className="text-sm font-medium">Document Preview</span>
              </div>
              <div className="p-6 space-y-4 font-mono text-xs bg-secondary/20">
                <div className="text-center border-b border-border/30 pb-4">
                  <p className="font-bold text-base text-foreground">HDFC BANK</p>
                  <p className="text-muted-foreground">Statement of Account</p>
                  <p className="text-muted-foreground">Branch: Koramangala, Bengaluru</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-muted-foreground">
                  <p><span className="text-foreground">Name:</span> Rajesh Kumar Sharma</p>
                  <p><span className="text-foreground">A/C:</span> XXXX XXXX 4521</p>
                  <p><span className="text-foreground">Period:</span> Jan 2025</p>
                  <p><span className="text-foreground">IFSC:</span> HDFC0001234</p>
                </div>

                <div className="border border-border/30 rounded overflow-hidden">
                  <div className="grid grid-cols-5 gap-0 bg-primary/10 text-primary font-semibold">
                    <div className="p-2">Date</div>
                    <div className="p-2">Description</div>
                    <div className="p-2 text-right">Credit</div>
                    <div className="p-2 text-right">Debit</div>
                    <div className="p-2 text-right">Balance</div>
                  </div>
                  {transactions.map((t, i) => (
                    <div key={i} className="grid grid-cols-5 gap-0 border-t border-border/20 hover:bg-primary/5 transition-colors">
                      <div className="p-2">{t.date}</div>
                      <div className="p-2 truncate">{t.desc}</div>
                      <div className="p-2 text-right text-success">{t.credit}</div>
                      <div className="p-2 text-right text-destructive">{t.debit}</div>
                      <div className="p-2 text-right">{t.balance}</div>
                    </div>
                  ))}
                </div>

                <div className="flex justify-between pt-2 text-muted-foreground">
                  <p><span className="text-foreground">Opening:</span> ₹1,24,567.89</p>
                  <p><span className="text-foreground">Closing:</span> ₹1,87,234.56</p>
                </div>
              </div>
            </motion.div>

            {/* Right: Extracted Data */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="glass-card overflow-hidden"
            >
              <div className="p-4 border-b border-border/50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain size={16} className="text-primary" />
                  <span className="text-sm font-medium">Extracted Data</span>
                </div>
                <span className="text-xs text-muted-foreground">11 fields extracted</span>
              </div>

              <div className="divide-y divide-border/30">
                {fields.map((field) => (
                  <div key={field.key} className="p-4 hover:bg-secondary/30 transition-colors">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-muted-foreground">{field.label}</span>
                          <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${confidenceBg(field.confidence)} ${confidenceColor(field.confidence)}`}>
                            {field.confidence}%
                          </span>
                          {field.confidence < 75 && <AlertTriangle size={12} className="text-warning" />}
                        </div>

                        {editingKey === field.key ? (
                          <div className="flex items-center gap-2">
                            <input
                              value={editValue}
                              onChange={(e) => setEditValue(e.target.value)}
                              className="flex-1 px-2 py-1 rounded bg-secondary border border-primary/30 text-sm font-medium text-foreground outline-none focus:border-primary"
                              autoFocus
                            />
                            <button
                              onClick={() => saveEdit(field.key)}
                              className="h-7 w-7 rounded bg-primary/20 flex items-center justify-center hover:bg-primary/30 transition-colors"
                            >
                              <Save size={12} className="text-primary" />
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <p className={`text-sm font-medium ${field.corrected ? "text-primary" : ""}`}>
                              {field.corrected || field.value}
                            </p>
                            {field.corrected && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary/10 text-primary">corrected</span>
                            )}
                          </div>
                        )}
                      </div>

                      {editingKey !== field.key && (
                        <button
                          onClick={() => startEdit(field)}
                          className="h-7 w-7 rounded bg-secondary flex items-center justify-center hover:bg-secondary/80 transition-colors shrink-0 mt-1"
                        >
                          <Edit3 size={12} className="text-muted-foreground" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Validation section */}
              <div className="p-4 border-t border-border/50">
                <button
                  onClick={() => setShowTransactions(!showTransactions)}
                  className="flex items-center gap-2 text-sm font-medium w-full"
                >
                  <CheckCircle2 size={14} className="text-success" />
                  Validation Checks
                  {showTransactions ? <ChevronUp size={14} className="ml-auto" /> : <ChevronDown size={14} className="ml-auto" />}
                </button>
                {showTransactions && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    className="mt-3 space-y-2"
                  >
                    {[
                      { check: "Balance continuity verified", pass: true },
                      { check: "Date sequencing valid", pass: true },
                      { check: "Salary matches employer pattern", pass: false },
                      { check: "Cross-document consistency", pass: true },
                    ].map((v) => (
                      <div key={v.check} className="flex items-center gap-2 text-xs">
                        {v.pass ? (
                          <CheckCircle2 size={12} className="text-success" />
                        ) : (
                          <AlertTriangle size={12} className="text-warning" />
                        )}
                        <span className={v.pass ? "text-muted-foreground" : "text-warning"}>{v.check}</span>
                      </div>
                    ))}
                  </motion.div>
                )}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Reviewer;
