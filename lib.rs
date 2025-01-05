use anchor_lang::prelude::*;
use solana_program::system_instruction;

declare_id!("3BGrehnLwFC5tPsmB8SQ4UZgUDa2EMyzBVVb5KMxPbVc");

#[derive(AnchorSerialize, AnchorDeserialize, Clone, Debug)]
pub struct Party {
    pub name: String,
    pub votes: u64,
}

#[program]
pub mod VotingProgram {
    use super::*;

    pub fn initialize(ctx: Context<Initialize>, owner: Pubkey, bump: u8) -> Result<()> {
        let vote_account = &mut ctx.accounts.vote_account;
        vote_account.owner = owner;
        vote_account.bump = bump;

        vote_account.parties = vec![
            Party { name: String::from("PDP"), votes: 0 },
            Party { name: String::from("APC"), votes: 0 },
            Party { name: String::from("APGA"), votes: 0 },
        ];
        Ok(())
    }

    pub fn cast_vote(ctx: Context<CastVote>, partyname: String) -> Result<()> {
        let vote_account = &mut ctx.accounts.vote_account;
        
        if let Some(party) = vote_account.parties.iter_mut().find(|p| p.name == partyname) {
            party.votes += 1;
            Ok(())
        } else {
            Err(ErrorCode::InvalidParty.into())
        }
    }

    pub fn calculate_winner(ctx: Context<DisplayVotes>) -> Result<()> {
        let vote_account = &ctx.accounts.vote_account;
        
        // Print all party results
        msg!("Vote Results:");
        for party in &vote_account.parties {
            msg!("Party: {}, Votes: {}", party.name, party.votes);
        }
        
        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(bump: u8)]
pub struct Initialize<'info> {
    #[account(
        init,
        seeds = [b"vxtx"],
        bump,
        payer = user,
        space = 8 + 32 + 1 + (3 * (32 + 8))
    )]
    pub vote_account: Account<'info, VoteAccount>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct CastVote<'info> {
    #[account(mut)]
    pub vote_account: Account<'info, VoteAccount>,
}

#[derive(Accounts)]
pub struct DisplayVotes<'info> {
    pub vote_account: Account<'info, VoteAccount>,
}

#[account]
pub struct VoteAccount {
    pub owner: Pubkey,
    pub bump: u8,
    pub parties: Vec<Party>,
}

#[account]
pub struct Winner {
    pub winner: String,
    pub votes: u64,
    pub is_winner: bool,
}

#[error_code]
pub enum ErrorCode {
    #[msg("Invalid party name provided")]
    InvalidParty,
    #[msg("No parties initialized")]
    NoParties,
}