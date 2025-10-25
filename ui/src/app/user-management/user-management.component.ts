
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';

@Component({
  selector: 'app-user-management',
  standalone: true,
  imports: [CommonModule, MatTableModule],
  templateUrl: './user-management.component.html',
  styleUrls: ['./user-management.component.scss']
})
export class UserManagementComponent implements OnInit {
  displayedColumns: string[] = ['name', 'email', 'role'];
  dataSource = [
    {name: 'John Doe', email: 'john.doe@example.com', role: 'Admin'},
    {name: 'Jane Smith', email: 'jane.smith@example.com', role: 'User'},
  ];

  constructor() { }

  ngOnInit(): void {
  }

}
