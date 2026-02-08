import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import ProductOverview from "./pages/ProductOverview";
import Upload from "./pages/Upload";
import Reviewer from "./pages/Reviewer";
import Dashboard from "./pages/Dashboard";
import Architecture from "./pages/Architecture";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Index />} />
          <Route path="/product" element={<ProductOverview />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/reviewer" element={<Reviewer />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/architecture" element={<Architecture />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
