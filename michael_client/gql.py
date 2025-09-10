"""
Created by Michael Wilson, Senior Software Engineer

09/09/2025 - Updated the file to added in the GET_DEVICES, TRACKS,DETECTION 
"""

INTROSPECTION = """
query IntrospectionQuery {
  __schema {
    types {
      name
      kind
      description
      fields {
        name
        type { name kind }
        description
      }
    }
  }
}
"""

GET_DEVICES = """
query GetDevices($limit: Int, $offset: Int) {
  devices(limit: $limit, offset: $offset) {
    id
    name
    type
    status
    location { latitude longitude altitude }
    lastSeen
    batteryLevel
    firmwareVersion
    metadata
    tags
  }
}
"""

GET_DEVICE = """
query GetDevice($deviceId: ID!) {
  device(id: $deviceId) {
    id
    name
    type
    status
    location { latitude longitude altitude }
    lastSeen
    batteryLevel
    firmwareVersion
    metadata
    tracks { id startTime endTime totalDistance averageSpeed }
    recentDetections(limit: 10) {
      id timestamp detectionType confidence
      location { latitude longitude }
    }
  }
}
"""

GET_TRACKS = """
query GetTracks($deviceId: ID, $startTime: DateTime, $endTime: DateTime, $limit: Int) {
  tracks(deviceId: $deviceId, startTime: $startTime, endTime: $endTime, limit: $limit) {
    id deviceId startTime endTime totalDistance averageSpeed maxSpeed
    points {
      timestamp
      location { latitude longitude altitude }
      speed heading
    }
    metadata
  }
}
"""

GET_DETECTIONS = """
query GetDetections($deviceId: ID, $detectionType: String, $startTime: DateTime,
                    $endTime: DateTime, $limit: Int, $minConfidence: Float) {
  detections(deviceId: $deviceId, detectionType: $detectionType, startTime: $startTime,
             endTime: $endTime, limit: $limit, minConfidence: $minConfidence) {
    id deviceId timestamp detectionType confidence
    location { latitude longitude altitude }
    boundingBox { x y width height }
    metadata
    associatedTrack { id startTime endTime }
  }
}
"""

CREATE_EVENT = """
mutation CreateEvent($input: CreateEventInput!) {
  createEvent(input: $input) {
    id name type timestamp deviceId
    location { latitude longitude altitude }
    metadata createdAt updatedAt
  }
}
"""

SUB_DETECTIONS = """
subscription NewDetections($deviceId: ID, $detectionType: String, $minConfidence: Float) {
  detectionCreated(deviceId: $deviceId, detectionType: $detectionType, minConfidence: $minConfidence) {
    id deviceId timestamp detectionType confidence
    location { latitude longitude altitude }
    metadata
  }
}
"""
