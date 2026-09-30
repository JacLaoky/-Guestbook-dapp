// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Guestbook - an on-chain guestbook with likes and tips
/// @notice Anyone can post a message, like a message once, and tip the author in ETH.
contract Guestbook {
    struct Entry {
        address author;
        string text;
        uint256 timestamp;
        uint256 likes;
        uint256 tips; // total wei tipped to this entry
    }

    Entry[] public entries;

    // entryId => user => has this user liked the entry?
    mapping(uint256 => mapping(address => bool)) public hasLiked;

    event NewEntry(uint256 indexed id, address indexed author, string text);
    event Liked(uint256 indexed id, address indexed user);
    event Tipped(uint256 indexed id, address indexed from, uint256 amount);

    /// @notice Post a new message (1 to 280 bytes).
    function post(string calldata text) external {
        require(bytes(text).length > 0, "Message is empty");
        require(bytes(text).length <= 280, "Message is too long");

        entries.push(Entry(msg.sender, text, block.timestamp, 0, 0));
        emit NewEntry(entries.length - 1, msg.sender, text);
    }

    /// @notice Like a message. Each address can like a message only once.
    function like(uint256 id) external {
        require(id < entries.length, "Entry does not exist");
        require(!hasLiked[id][msg.sender], "Already liked");

        hasLiked[id][msg.sender] = true;
        entries[id].likes += 1;
        emit Liked(id, msg.sender);
    }

    /// @notice Tip the author of a message. The ETH goes straight to the author.
    function tip(uint256 id) external payable {
        require(id < entries.length, "Entry does not exist");
        require(msg.value > 0, "Tip must be greater than 0");

        Entry storage e = entries[id];
        require(e.author != msg.sender, "Cannot tip yourself");

        e.tips += msg.value; // update state first, then send ETH
        (bool ok, ) = payable(e.author).call{value: msg.value}("");
        require(ok, "Transfer failed");

        emit Tipped(id, msg.sender, msg.value);
    }

    /// @notice Total number of messages.
    function count() external view returns (uint256) {
        return entries.length;
    }

    /// @notice Return all messages (fine for a small class project).
    function getAll() external view returns (Entry[] memory) {
        return entries;
    }
}
