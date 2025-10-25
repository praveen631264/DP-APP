
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';

@Component({
  selector: 'app-audit-log',
  standalone: true,
  imports: [CommonModule, MatTableModule],
  templateUrl: './audit-log.component.html',
  styleUrls: ['./audit-log.component.scss']
})
export class AuditLogComponent implements OnInit {
  displayedColumns: string[] = ['timestamp', 'user', 'action', 'details'];
  dataSource = [
    {timestamp: new Date(), user: 'admin@example.com', action: 'Logged In', details: 'User logged in successfully'},
    {timestamp: new Date(), user: 'user@example.com', action: 'Uploaded Document', details: 'Document \'test.pdf\' uploaded'},
  ];

  constructor() { }

  ngOnInit(): void {
  }

}
