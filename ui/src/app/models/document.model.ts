
export interface AuditLog {
    event_name: string;
    timestamp: string;
    details: any;
}

export interface Document {
    id: string;
    filename: string;
    content_type: string;
    status: string;
    category: string;
    kvps: { [key: string]: any };
    audit_trail: AuditLog[];
    created_at: string;
    updated_at: string;
    _version: number;
}
