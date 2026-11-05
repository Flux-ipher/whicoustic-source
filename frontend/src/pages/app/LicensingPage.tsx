import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { EmptyInboxIllustration } from '../../components/ui/Illustrations';
import { PageTransition } from '../../components/ui/PageTransition';
import { mockLicensingRequests, LicensingRequest } from '../../data/mock/licensing';
import { FileCheck2, Check, X, ShieldCheck, DollarSign, Filter, Eye, RotateCcw } from 'lucide-react';

export const LicensingPage: React.FC = () => {
  const [requests, setRequests] = useState<LicensingRequest[]>(mockLicensingRequests);
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'APPROVED' | 'REJECTED'>('ALL');
  const [selectedReq, setSelectedReq] = useState<LicensingRequest | null>(null);

  const filteredRequests = requests.filter((r) => filter === 'ALL' || r.status === filter);

  const handleApprove = (id: string) => {
    setRequests((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'APPROVED' } : r))
    );
    setSelectedReq(null);
  };

  const handleReject = (id: string) => {
    setRequests((prev) =>
      prev.map((r) => (r.id === id ? { ...r, status: 'REJECTED' } : r))
    );
    setSelectedReq(null);
  };

  return (
    <PageTransition className="space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-outline-subtle">
        <div className="space-y-1">
          <h2 className="font-recoleta text-3xl font-bold text-on-surface">
            Studio Licensing Inbound Requests
          </h2>
          <p className="font-berthold text-xs text-slate-600">
            Review production proposals, usage scopes, and automated royalty splits before granting neural weights access.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 bg-surface-container p-1 rounded-pill">
          {(['ALL', 'PENDING', 'APPROVED', 'REJECTED'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-3 py-1 rounded-pill text-xs font-berthold font-semibold transition-all ${
                filter === tab ? 'bg-white text-on-surface shadow-sm' : 'text-secondary hover:text-on-surface'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Requests Table or Empty State */}
      <Card elevation="elevated" padding="none">
        {filteredRequests.length === 0 ? (
          <div className="py-8">
            <EmptyState
              illustration={<EmptyInboxIllustration size={170} />}
              title={`No ${filter === 'ALL' ? '' : filter.toLowerCase()} licensing proposals`}
              description={
                filter === 'ALL'
                  ? 'Your licensing queue is currently clear. Publish your voice persona on the Voice IP Marketplace to receive studio casting inquiries.'
                  : `There are currently 0 licensing inquiries marked as ${filter}. Reset the status filter to see all production requests.`
              }
              actionLabel={filter !== 'ALL' ? 'Show All Requests' : 'View Voice Marketplace'}
              onAction={filter !== 'ALL' ? () => setFilter('ALL') : undefined}
              actionHref={filter === 'ALL' ? '/marketplace' : undefined}
              actionIcon={filter !== 'ALL' ? <RotateCcw className="w-4 h-4" /> : undefined}
            />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-berthold">
              <thead className="bg-surface-container text-secondary uppercase tracking-wider font-semibold border-b border-outline-subtle">
                <tr>
                  <th className="py-3.5 px-6">Licensee / Studio</th>
                  <th className="py-3.5 px-4">Production Title</th>
                  <th className="py-3.5 px-4">Category</th>
                  <th className="py-3.5 px-4">Territory</th>
                  <th className="py-3.5 px-4">Proposed Upfront</th>
                  <th className="py-3.5 px-4">Royalty Split</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-subtle">
                <AnimatePresence>
                  {filteredRequests.map((req) => (
                    <motion.tr
                      key={req.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="hover:bg-surface-container-low transition-colors"
                    >
                      <td className="py-4 px-6 font-bold text-on-surface">
                        <p>{req.studioName}</p>
                        <span className="text-[11px] font-code text-secondary font-normal">{req.id}</span>
                      </td>
                      <td className="py-4 px-4 font-semibold text-on-surface">{req.projectTitle}</td>
                      <td className="py-4 px-4 text-secondary">{req.projectType}</td>
                      <td className="py-4 px-4 text-secondary">{req.territory}</td>
                      <td className="py-4 px-4 font-recoleta text-sm font-bold text-on-surface">
                        ${req.proposedFee.toLocaleString()}
                      </td>
                      <td className="py-4 px-4 font-code font-bold text-primary-container">
                        {req.royaltySplitPct}%
                      </td>
                      <td className="py-4 px-4">
                        <span
                          className={`text-xs font-medium ${
                            req.status === 'APPROVED'
                              ? 'text-emerald-700'
                              : req.status === 'REJECTED'
                              ? 'text-slate-500'
                              : 'text-amber-700'
                          }`}
                        >
                          {req.status}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {req.status === 'PENDING' ? (
                            <>
                              <Button
                                variant="primary"
                                size="sm"
                                onClick={() => handleApprove(req.id)}
                                icon={<Check className="w-3.5 h-3.5" />}
                              >
                                Approve
                              </Button>
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => handleReject(req.id)}
                                icon={<X className="w-3.5 h-3.5 text-error" />}
                              >
                                Decline
                              </Button>
                            </>
                          ) : (
                            <button
                              onClick={() => setSelectedReq(req)}
                              className="text-secondary hover:text-on-surface p-1.5"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </PageTransition>
  );
};

