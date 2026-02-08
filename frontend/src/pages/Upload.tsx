import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload as UploadIcon,
  FileText,
  CheckCircle2,
  AlertCircle,
  Clock,
  X,
  Eye,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

interface DocFile {
  id: string;
  name: string;
  status: "uploading" | "classifying" | "extracting" | "validating" | "done" | "review";
  type?: string;
  confidence?: number;
}

const statusLabels: Record<string, { label: string; color: string }> = {
  uploading: { label: "Uploading", color: "text-muted-foreground" },
  classifying: { label: "Classifying", color: "text-warning" },
  extracting: { label: "Extracting", color: "text-warning" },
  validating: { label: "Validating", color: "text-warning" },
  done: { label: "Validated", color: "text-success" },
  review: { label: "Needs Review", color: "text-warning" },
};

const mockDocs: DocFile[] = [
  { id: "1", name: "HDFC_Statement_Jan2025.pdf", status: "done", type: "Bank Statement", confidence: 97.3 },
  { id: "2", name: "Payslip_Dec2024.pdf", status: "done", type: "Payslip", confidence: 94.8 },
  { id: "3", name: "Settlement_Letter.pdf", status: "review", type: "Settlement Letter", confidence: 72.1 },
];

const Upload = () => {
  const [files, setFiles] = useState<DocFile[]>(mockDocs);
  const [dragOver, setDragOver] = useState(false);

  const simulateUpload = (name: string) => {
    const id = Date.now().toString();
    const newFile: DocFile = { id, name, status: "uploading" };
    setFiles((prev) => [newFile, ...prev]);

    const stages: DocFile["status"][] = ["classifying", "extracting", "validating", "done"];
    const types = ["Bank Statement", "Invoice", "Payslip", "Agreement"];

    stages.forEach((stage, i) => {
      setTimeout(() => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === id
              ? {
                  ...f,
                  status: stage,
                  type: i >= 1 ? types[Math.floor(Math.random() * types.length)] : undefined,
                  confidence: stage === "done" ? 85 + Math.random() * 14 : undefined,
                }
              : f
          )
        );
      }, (i + 1) * 1200);
    });
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const dropped = Array.from(e.dataTransfer.files);
    dropped.forEach((f) => simulateUpload(f.name));
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <section className="pt-28 pb-16">
        <div className="container max-w-4xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-10"
          >
            <h1 className="text-3xl font-bold mb-3">
              Upload & <span className="gradient-text">Process</span>
            </h1>
            <p className="text-muted-foreground">
              Drop any financial document. Watch it get classified, extracted, and validated in real-time.
            </p>
          </motion.div>

          {/* Upload zone */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => simulateUpload("Document_" + Date.now().toString().slice(-6) + ".pdf")}
            className={`glass-card p-12 text-center cursor-pointer transition-all mb-8 ${
              dragOver ? "border-primary glow" : "hover:border-primary/30"
            }`}
          >
            <UploadIcon className="mx-auto mb-4 text-primary" size={40} />
            <p className="font-medium mb-1">Drop files here or click to upload</p>
            <p className="text-sm text-muted-foreground">
              PDF, PNG, JPG — Bank statements, payslips, invoices, agreements
            </p>
          </motion.div>

          {/* File list */}
          <div className="space-y-3">
            <AnimatePresence>
              {files.map((file) => {
                const statusInfo = statusLabels[file.status];
                const isProcessing = ["uploading", "classifying", "extracting", "validating"].includes(file.status);
                return (
                  <motion.div
                    key={file.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    className="glass-card p-4 flex items-center gap-4"
                  >
                    <div className="h-10 w-10 rounded-lg bg-secondary flex items-center justify-center shrink-0">
                      <FileText className="text-primary" size={20} />
                    </div>

                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{file.name}</p>
                      <div className="flex items-center gap-3 mt-1">
                        {file.type && (
                          <span className="text-xs text-muted-foreground">{file.type}</span>
                        )}
                        <span className={`text-xs font-medium flex items-center gap-1 ${statusInfo.color}`}>
                          {isProcessing && <Clock size={12} className="animate-spin" />}
                          {file.status === "done" && <CheckCircle2 size={12} />}
                          {file.status === "review" && <AlertCircle size={12} />}
                          {statusInfo.label}
                        </span>
                      </div>

                      {isProcessing && (
                        <div className="mt-2 h-1 bg-secondary rounded-full overflow-hidden">
                          <motion.div
                            className="h-full bg-primary rounded-full"
                            initial={{ width: "0%" }}
                            animate={{ width: file.status === "classifying" ? "30%" : file.status === "extracting" ? "60%" : file.status === "validating" ? "85%" : "10%" }}
                            transition={{ duration: 0.5 }}
                          />
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {file.confidence && (
                        <span className={`text-xs font-mono px-2 py-1 rounded-md ${
                          file.confidence > 90
                            ? "bg-success/10 text-success"
                            : "bg-warning/10 text-warning"
                        }`}>
                          {file.confidence.toFixed(1)}%
                        </span>
                      )}
                      {file.status === "done" && (
                        <button className="h-8 w-8 rounded-md bg-secondary flex items-center justify-center hover:bg-secondary/80 transition-colors">
                          <Eye size={14} className="text-muted-foreground" />
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setFiles((prev) => prev.filter((f) => f.id !== file.id));
                        }}
                        className="h-8 w-8 rounded-md bg-secondary flex items-center justify-center hover:bg-destructive/20 transition-colors"
                      >
                        <X size={14} className="text-muted-foreground" />
                      </button>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Upload;
