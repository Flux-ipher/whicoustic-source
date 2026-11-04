import React, { useState } from 'react';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { mockLicensingRequests, LicensingRequest } from '../../data/mock/licensing';
import { FileCheck2, Check, X, ShieldCheck, DollarSign, Filter, Eye } from 'lucide-react';

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
    <div className="space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-outline-subtle">
        <div className="space-y-1">
          <Badge variant="amber" size="sm" icon={<FileCheck2 className="w-3.5 h-3.5" />}>
            Smart Contract Approvals
          </Badge>
          <h2 className="font-recoletta text-3xl font-bold text-on-surface">
            Studio Licensing Inbound Requests
          </h2>
          <p className="font-lora italic text-xs text-secondary">
            Review production proposals, usage scopes, and smart contract royalty splits before granting neural weights access.
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

      {/* Requests Table */}
      <Card elevation="elevated" padding="none">
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
              {filteredRequests.map((req) => (
                <tr key={req.id} className="hover:bg-surface-container-low transition-colors">
                  <td className="py-4 px-6 font-bold text-on-surface">
                    <p>{req.studioName}</p>
                    <span className="text-[11px] font-code text-secondary font-normal">{req.id}</span>
                  </td>
                  <td className="py-4 px-4 font-semibold text-on-surface">{req.projectTitle}</td>
                  <td className="py-4 px-4 text-secondary">{req.projectType}</td>
                  <td className="py-4 px-4 text-secondary">{req.territory}</td>
                  <td className="py-4 px-4 font-recoletta text-sm font-bold text-on-surface">
                    ${req.proposedFee.toLocaleString()}
                  </td>
                  <td className="py-4 px-4 font-code font-bold text-primary-container">
                    {req.royaltySplitPct}%
                  </td>
                  <td className="py-4 px-4">
                    <Badge
                      variant={
                        req.status === 'APPROVED' ? 'success' : req.status === 'REJECTED' ? 'neutral' : 'amber'
                      }
                      size="sm"
                    >
                      {req.status}
                    </Badge>
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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
