'use client';

import { MapPin, Star, Briefcase, Award, Phone, Mail } from 'lucide-react';
import Link from 'next/link';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { AgentProfile } from '@/lib/types';

interface AgentCardProps {
  agent: AgentProfile;
  locale: string;
}

export function AgentCard({ agent, locale }: AgentCardProps) {
  const displayName = agent.name || agent.professional_email?.split('@')[0] || 'Agent';

  return (
    <Card className="group overflow-hidden transition-all hover:shadow-lg">
      <CardContent className="p-0">
        <div className="flex flex-col sm:flex-row">
          {/* Avatar Section */}
          <div className="flex-shrink-0 p-4 sm:p-6">
            <div className="relative">
              {agent.profile_image_url ? (
                <img
                  src={agent.profile_image_url}
                  alt={displayName}
                  className="h-24 w-24 rounded-full object-cover"
                />
              ) : (
                <div className="flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-purple-600 text-2xl font-bold text-white">
                  {displayName.charAt(0).toUpperCase()}
                </div>
              )}
              {agent.is_verified && (
                <div className="absolute -bottom-1 -right-1 rounded-full bg-green-500 p-1.5">
                  <Award className="h-4 w-4 text-white" />
                </div>
              )}
            </div>
          </div>

          {/* Info Section */}
          <div className="flex-1 p-4 sm:py-6 sm:pr-6">
            <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
              <div>
                <h3 className="text-lg font-semibold">{displayName}</h3>
                {agent.agency_name && (
                  <p className="text-sm text-muted-foreground">{agent.agency_name}</p>
                )}
              </div>
              {agent.is_verified && (
                <Badge variant="secondary" className="bg-green-100 text-green-800">
                  Verified
                </Badge>
              )}
            </div>

            {/* Rating and Stats */}
            <div className="mb-3 flex flex-wrap items-center gap-4 text-sm">
              {agent.average_rating > 0 && (
                <div className="flex items-center gap-1">
                  <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                  <span className="font-medium">{agent.average_rating.toFixed(1)}</span>
                  <span className="text-muted-foreground">({agent.total_reviews} reviews)</span>
                </div>
              )}
              {agent.total_sales > 0 && (
                <div className="flex items-center gap-1 text-muted-foreground">
                  <Briefcase className="h-4 w-4" />
                  <span>{agent.total_sales} sales</span>
                </div>
              )}
            </div>

            {/* Specialties */}
            {agent.specialties && agent.specialties.length > 0 && (
              <div className="mb-3 flex flex-wrap gap-1.5">
                {agent.specialties.slice(0, 3).map((specialty) => (
                  <Badge key={specialty} variant="outline" className="text-xs">
                    {specialty}
                  </Badge>
                ))}
                {agent.specialties.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{agent.specialties.length - 3}
                  </Badge>
                )}
              </div>
            )}

            {/* Service Areas */}
            {agent.service_areas && agent.service_areas.length > 0 && (
              <div className="mb-3 flex items-center gap-1 text-sm text-muted-foreground">
                <MapPin className="h-4 w-4" />
                <span>{agent.service_areas.slice(0, 2).join(', ')}</span>
                {agent.service_areas.length > 2 && (
                  <span>+{agent.service_areas.length - 2} more</span>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap gap-2">
              <Link href={`/${locale}/agents/${agent.id}`}>
                <Button variant="outline" size="sm">
                  View Profile
                </Button>
              </Link>
              {agent.professional_phone && (
                <a href={`tel:${agent.professional_phone}`}>
                  <Button variant="ghost" size="sm">
                    <Phone className="mr-1 h-4 w-4" />
                    Call
                  </Button>
                </a>
              )}
              {agent.professional_email && (
                <a href={`mailto:${agent.professional_email}`}>
                  <Button variant="ghost" size="sm">
                    <Mail className="mr-1 h-4 w-4" />
                    Email
                  </Button>
                </a>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
