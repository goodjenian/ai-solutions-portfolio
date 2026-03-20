#!/usr/bin/env python3
"""Add new tasks to Task Master."""

import json
from datetime import datetime


def main():
    """Add new tasks to Task Master."""
    # Read current tasks
    with open(".taskmaster/tasks/tasks.json", "r", encoding="utf-8") as f:
        current = json.load(f)

    # New tasks to add
    new_tasks = [
        {
            "id": "19",
            "title": "[TASK-019] Investment Property Analyzer",
            "description": (
                "Comprehensive investment analysis tools including "
                "ROI, cash flow, cap rate, and rental yield calculations."
            ),
            "status": "pending",
            "priority": "high",
            "subtasks": [
                {
                    "id": 19.1,
                    "title": "[TASK-019.1] ROI & Cash Flow Calculator",
                    "status": "pending",
                    "parentId": "19",
                },
                {
                    "id": 19.2,
                    "title": "[TASK-019.2] Cap Rate & Yield Analysis",
                    "status": "pending",
                    "parentId": "19",
                },
                {
                    "id": 19.3,
                    "title": "[TASK-019.3] Investment Property Scoring",
                    "status": "pending",
                    "parentId": "19",
                },
                {
                    "id": 19.4,
                    "title": "[TASK-019.4] Investment Comparison UI",
                    "status": "pending",
                    "parentId": "19",
                },
            ],
            "dependencies": ["5", "7"],
            "updatedAt": datetime.now().isoformat() + "Z",
        },
        {
            "id": "20",
            "title": "[TASK-020] Neighborhood Quality Index",
            "description": (
                "Composite neighborhood scoring combining safety, schools, "
                "amenities, walkability, and green space."
            ),
            "status": "pending",
            "priority": "high",
            "subtasks": [
                {
                    "id": 20.1,
                    "title": "[TASK-020.1] Data Integration Layer",
                    "status": "pending",
                    "parentId": "20",
                },
                {
                    "id": 20.2,
                    "title": "[TASK-020.2] Scoring Algorithm",
                    "status": "pending",
                    "parentId": "20",
                },
                {
                    "id": 20.3,
                    "title": "[TASK-020.3] API & Endpoints",
                    "status": "pending",
                    "parentId": "20",
                },
                {
                    "id": 20.4,
                    "title": "[TASK-020.4] UI Integration",
                    "status": "pending",
                    "parentId": "20",
                },
            ],
            "dependencies": ["5", "7"],
            "updatedAt": datetime.now().isoformat() + "Z",
        },
        {
            "id": "21",
            "title": "[TASK-021] Commute Time Analysis",
            "description": (
                "Isochrone-based commute analysis using Google Routes API "
                "or TravelTime API with property ranking."
            ),
            "status": "pending",
            "priority": "medium",
            "subtasks": [
                {
                    "id": 21.1,
                    "title": "[TASK-021.1] Isochrone API Integration",
                    "status": "pending",
                    "parentId": "21",
                },
                {
                    "id": 21.2,
                    "title": "[TASK-021.2] Property Ranking by Commute",
                    "status": "pending",
                    "parentId": "21",
                },
                {
                    "id": 21.3,
                    "title": "[TASK-021.3] Map Visualization",
                    "status": "pending",
                    "parentId": "21",
                },
                {
                    "id": 21.4,
                    "title": "[TASK-021.4] UI Components",
                    "status": "pending",
                    "parentId": "21",
                },
            ],
            "dependencies": ["7"],
            "updatedAt": datetime.now().isoformat() + "Z",
        },
        {
            "id": "22",
            "title": "[TASK-022] Total Cost of Ownership Calculator",
            "description": (
                "Extend mortgage calculator with utilities, parking, taxes, "
                "insurance, maintenance, and HOA."
            ),
            "status": "pending",
            "priority": "high",
            "subtasks": [
                {
                    "id": 22.1,
                    "title": "[TASK-022.1] Cost Categories Extension",
                    "status": "pending",
                    "parentId": "22",
                },
                {
                    "id": 22.2,
                    "title": "[TASK-022.2] Calculation Logic",
                    "status": "pending",
                    "parentId": "22",
                },
                {
                    "id": 22.3,
                    "title": "[TASK-022.3] UI Enhancements",
                    "status": "pending",
                    "parentId": "22",
                },
                {
                    "id": 22.4,
                    "title": "[TASK-022.4] Export & Sharing",
                    "status": "pending",
                    "parentId": "22",
                },
            ],
            "dependencies": [],
            "updatedAt": datetime.now().isoformat() + "Z",
        },
        {
            "id": "23",
            "title": "[TASK-023] AI Listing Generator",
            "description": (
                "LLM-powered property description, headline, and social media content generation."
            ),
            "status": "pending",
            "priority": "medium",
            "subtasks": [
                {
                    "id": 23.1,
                    "title": "[TASK-023.1] Description Generation",
                    "status": "pending",
                    "parentId": "23",
                },
                {
                    "id": 23.2,
                    "title": "[TASK-023.2] Headline & Subject Lines",
                    "status": "pending",
                    "parentId": "23",
                },
                {
                    "id": 23.3,
                    "title": "[TASK-023.3] Social Media Content",
                    "status": "pending",
                    "parentId": "23",
                },
                {
                    "id": 23.4,
                    "title": "[TASK-023.4] Multilingual Support",
                    "status": "pending",
                    "parentId": "23",
                },
            ],
            "dependencies": ["5"],
            "updatedAt": datetime.now().isoformat() + "Z",
        },
        {
            "id": "24",
            "title": "[TASK-024] Lead Scoring & Agent Analytics",
            "description": (
                "Score leads by likelihood to close, track agent performance, "
                "and optimize lead distribution."
            ),
            "status": "pending",
            "priority": "medium",
            "subtasks": [
                {
                    "id": 24.1,
                    "title": "[TASK-024.1] Lead Scoring Model",
                    "status": "pending",
                    "parentId": "24",
                },
                {
                    "id": 24.2,
                    "title": "[TASK-024.2] Agent Performance Tracking",
                    "status": "pending",
                    "parentId": "24",
                },
                {
                    "id": 24.3,
                    "title": "[TASK-024.3] Lead Routing Optimization",
                    "status": "pending",
                    "parentId": "24",
                },
                {
                    "id": 24.4,
                    "title": "[TASK-024.4] Analytics Dashboard",
                    "status": "pending",
                    "parentId": "24",
                },
            ],
            "dependencies": ["6", "7"],
            "updatedAt": datetime.now().isoformat() + "Z",
        },
    ]

    # Add new tasks to existing
    current["master"]["tasks"].extend(new_tasks)

    # Update metadata
    current["master"]["metadata"]["taskCount"] = len(current["master"]["tasks"])
    completed = sum(1 for t in current["master"]["tasks"] if t.get("status") == "done")
    current["master"]["metadata"]["completedCount"] = completed
    current["master"]["metadata"]["lastModified"] = datetime.now().isoformat() + "Z"

    # Write back
    with open(".taskmaster/tasks/tasks.json", "w", encoding="utf-8") as f:
        json.dump(current, f, indent=2)

    print("Created 6 new tasks in Task Master")
    print(f"Total tasks: {current['master']['metadata']['taskCount']}")
    print(f"Completed: {completed}")
    print(f"Pending: {current['master']['metadata']['taskCount'] - completed}")


if __name__ == "__main__":
    main()
