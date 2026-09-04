// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MatchRegistry
 * @notice Stores tamper-evident records of verified Face ID matches against online / social media posts.
 * @dev Records contain SHA-256 hashes of the source image, numerical face embedding, matched URL,
 *      and calculated similarity score.
 */
contract MatchRegistry {
    struct MatchRecord {
        bytes32 imageHash;          // SHA-256 hash of original input image
        bytes32 encodingHash;       // SHA-256 hash of extracted 512-d face embedding vector
        string matchUrl;            // Matched social post / candidate source URL
        uint256 similarityScoreBps; // Similarity score in basis points (e.g., 9520 = 95.20%)
        uint256 timestamp;          // Block timestamp when match was recorded
        address recordedBy;         // Address that submitted the verification record
    }

    // Mapping from input image SHA-256 hash to its MatchRecord
    mapping(bytes32 => MatchRecord) public records;

    // List of all recorded image hashes for enumerability
    bytes32[] public recordedHashes;

    // Events for real-time tracking and indexing
    event MatchRecorded(
        bytes32 indexed imageHash,
        bytes32 indexed encodingHash,
        string matchUrl,
        uint256 similarityScoreBps,
        uint256 timestamp,
        address indexed recordedBy
    );

    /**
     * @notice Record a verified face match on-chain
     * @param _imageHash SHA-256 hash of input image (bytes32)
     * @param _encodingHash SHA-256 hash of face embedding (bytes32)
     * @param _matchUrl Verified URL of the matching social media post
     * @param _similarityScoreBps Similarity score scaled in basis points (0 to 10000)
     */
    function recordMatch(
        bytes32 _imageHash,
        bytes32 _encodingHash,
        string calldata _matchUrl,
        uint256 _similarityScoreBps
    ) external {
        require(_imageHash != bytes32(0), "Invalid image hash");
        require(bytes(_matchUrl).length > 0, "Match URL cannot be empty");
        require(_similarityScoreBps <= 10000, "Similarity score cannot exceed 10000 (100%)");
        require(records[_imageHash].timestamp == 0, "Record already exists for this image hash");

        records[_imageHash] = MatchRecord({
            imageHash: _imageHash,
            encodingHash: _encodingHash,
            matchUrl: _matchUrl,
            similarityScoreBps: _similarityScoreBps,
            timestamp: block.timestamp,
            recordedBy: msg.sender
        });

        recordedHashes.push(_imageHash);

        emit MatchRecorded(
            _imageHash,
            _encodingHash,
            _matchUrl,
            _similarityScoreBps,
            block.timestamp,
            msg.sender
        );
    }

    /**
     * @notice Retrieve the verification record for a given image hash
     * @param _imageHash SHA-256 hash of input image
     * @return MatchRecord struct with all stored attributes
     */
    function getMatch(bytes32 _imageHash) external view returns (MatchRecord memory) {
        require(records[_imageHash].timestamp > 0, "No record found for this image hash");
        return records[_imageHash];
    }

    /**
     * @notice Check if a record exists for a given image hash
     * @param _imageHash SHA-256 hash of input image
     * @return bool True if record exists, False otherwise
     */
    function hasRecord(bytes32 _imageHash) external view returns (bool) {
        return records[_imageHash].timestamp > 0;
    }

    /**
     * @notice Get total count of recorded matches
     * @return Total count of records
     */
    function totalRecords() external view returns (uint256) {
        return recordedHashes.length;
    }

    /**
     * @notice Get image hash by index in recordedHashes list
     * @param _index Index in array
     * @return bytes32 image hash
     */
    function getRecordedHashAtIndex(uint256 _index) external view returns (bytes32) {
        require(_index < recordedHashes.length, "Index out of bounds");
        return recordedHashes[_index];
    }
}
